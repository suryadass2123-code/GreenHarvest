from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import CheckoutForm
from .models import Cart, CartItem, Coupon, Notification, Order, OrderItem, RewardTransaction, ReturnRequest, Wishlist


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(customer=user)
    return cart

@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    items = cart.items.select_related('product')
    total = sum(item.subtotal for item in items)
    return render(request, 'orders/cart.html', {'cart': cart, 'items': items, 'total': total})

@login_required
def add_to_cart(request, product_id):
    from products.models import Product
    product = get_object_or_404(Product, id=product_id, is_available=True)
    quantity = max(int(request.POST.get('quantity', 1)), 1) if request.method == 'POST' else 1
    quantity = min(quantity, product.stock)
    cart = get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    item.quantity = min((item.quantity if not created else 0) + quantity, product.stock)
    item.save()
    messages.success(request, f'{product.name} added to cart.')
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    cart = get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1 or quantity > item.product.stock:
                raise ValueError
            item.quantity = quantity
            item.save()
        except ValueError:
            messages.error(request, 'Please enter a valid quantity.')
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request.user)
    get_object_or_404(CartItem, id=item_id, cart=cart).delete()
    return redirect('cart')

@login_required
def clear_cart(request):
    cart = get_or_create_cart(request.user)
    if request.method == 'POST':
        cart.items.all().delete()
    return redirect('cart')

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(customer=request.user).select_related('product', 'product__category')
    return render(request, 'orders/wishlist.html', {'wishlist': wishlist})

@login_required
def add_to_wishlist(request, product_id):
    from products.models import Product
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(customer=request.user, product=product)
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(customer=request.user, product_id=product_id).delete()
    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))

@login_required
def wishlist_toggle(request, product_id):
    from products.models import Product
    product = get_object_or_404(Product, id=product_id)
    obj = Wishlist.objects.filter(customer=request.user, product=product).first()
    if obj:
        obj.delete()
    else:
        Wishlist.objects.create(customer=request.user, product=product)
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


def calculate_coupon_discount(coupon, amount):
    if amount < coupon.minimum_amount:
        return Decimal('0.00')
    if coupon.discount_type == 'PERCENT':
        discount = amount * coupon.discount_value / Decimal('100')
        if coupon.maximum_discount > 0:
            discount = min(discount, coupon.maximum_discount)
    else:
        discount = coupon.discount_value
    return min(discount, amount)


def get_valid_coupon(code, amount):
    coupon = Coupon.objects.filter(code__iexact=code, active=True).first()
    if not coupon:
        return None, 'Invalid coupon code.'
    now = timezone.now()
    if coupon.valid_from and now < coupon.valid_from:
        return None, 'This coupon is not active yet.'
    if coupon.valid_until and now > coupon.valid_until:
        return None, 'This coupon has expired.'
    if coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit:
        return None, 'This coupon usage limit has been reached.'
    if amount < coupon.minimum_amount:
        return None, f'Minimum order amount is ₹{coupon.minimum_amount}.'
    return coupon, None

@login_required
def apply_coupon(request):
    if request.method != 'POST':
        return redirect('checkout')
    code = request.POST.get('code', '').strip()
    cart = get_or_create_cart(request.user)
    subtotal = sum(item.subtotal for item in cart.items.select_related('product'))
    coupon, error = get_valid_coupon(code, subtotal)
    if error:
        messages.error(request, error)
    else:
        request.session['coupon_code'] = coupon.code
        messages.success(request, f'Coupon {coupon.code} applied.')
    return redirect('checkout')

@login_required
def remove_coupon(request):
    request.session.pop('coupon_code', None)
    return redirect('checkout')

@login_required
def checkout(request):
    cart = get_or_create_cart(request.user)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cart_items = list(cart.items.select_related('product'))
                    subtotal = Decimal('0.00')
                    for item in cart_items:
                        if not item.product.is_available:
                            raise ValueError(f'{item.product.name} is unavailable.')
                        if item.quantity > item.product.stock:
                            raise ValueError(f'Only {item.product.stock} of {item.product.name} is available.')
                        subtotal += item.product.price * item.quantity
                    coupon = None
                    discount = Decimal('0.00')
                    code = request.session.get('coupon_code')
                    if code:
                        coupon, error = get_valid_coupon(code, subtotal)
                        if error:
                            request.session.pop('coupon_code', None)
                            raise ValueError(error)
                        discount = calculate_coupon_discount(coupon, subtotal)
                    order = Order.objects.create(
                        customer=request.user,
                        total_amount=subtotal - discount,
                        coupon=coupon,
                        discount_amount=discount,
                        payment_method=form.cleaned_data['payment_method'],
                        payment_status='PENDING', status='PENDING',
                        full_name=form.cleaned_data['full_name'], phone=form.cleaned_data['phone'],
                        address=form.cleaned_data['address'], city=form.cleaned_data['city'],
                        state=form.cleaned_data['state'], pincode=form.cleaned_data['pincode'], notes=form.cleaned_data['notes'],
                    )
                    for item in cart_items:
                        product = item.product
                        OrderItem.objects.create(order=order, product=product, product_name=product.name,
                                                 price=product.price, quantity=item.quantity,
                                                 subtotal=product.price * item.quantity)
                        product.stock -= item.quantity
                        product.is_available = product.stock > 0
                        product.save(update_fields=['stock', 'is_available'])
                    if coupon:
                        coupon.used_count += 1
                        coupon.save(update_fields=['used_count'])
                    cart.items.all().delete()
                    request.session.pop('coupon_code', None)
                    Notification.objects.create(user=request.user, title='Order Placed',
                                               message=f'Your order {order.order_number} was placed successfully.', notification_type='ORDER')
                if order.payment_method == 'ONLINE':
                    return redirect('payment_page', order_id=order.id)
                order.payment_status = 'COD_PENDING'
                order.save(update_fields=['payment_status'])
                return redirect('order_success', order_id=order.id)
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        profile = getattr(request.user, 'profile', None)
        form = CheckoutForm(initial={
            'full_name': request.user.get_full_name(),
            'phone': getattr(profile, 'phone', ''),
            'address': getattr(profile, 'address', ''),
            'city': getattr(profile, 'city', ''),
            'state': getattr(profile, 'state', 'Tamil Nadu'),
            'pincode': getattr(profile, 'pincode', ''),
        })
    items = cart.items.select_related('product')
    subtotal = sum(item.subtotal for item in items)
    coupon = None
    discount = Decimal('0.00')
    code = request.session.get('coupon_code')
    if code:
        coupon, _ = get_valid_coupon(code, subtotal)
        if coupon:
            discount = calculate_coupon_discount(coupon, subtotal)
    total = subtotal - discount
    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart, 'items': items, 'subtotal': subtotal, 'discount': discount, 'total': total, 'coupon': coupon})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, customer=request.user)
    return render(request, 'orders/order_success.html', {'order': order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related('items')
    return render(request, 'orders/my_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, customer=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def farmer_orders(request):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        return redirect('home')
    orders = Order.objects.filter(items__product__farmer=request.user).distinct().prefetch_related('items').order_by('-created_at')
    return render(request, 'orders/farmer_orders.html', {'orders': orders})


def award_reward_points(order):
    points = int(order.total_amount // Decimal('100'))
    if points <= 0 or RewardTransaction.objects.filter(order=order, transaction_type='EARN').exists():
        return
    profile = getattr(order.customer, 'profile', None)
    if not profile:
        return
    profile.reward_points += points
    profile.save(update_fields=['reward_points'])
    RewardTransaction.objects.create(customer=order.customer, order=order, points=points,
                                     transaction_type='EARN', description=f'Points earned for {order.order_number}')
    Notification.objects.create(user=order.customer, title='Reward Points Earned',
                                message=f'You earned {points} reward points.', notification_type='REWARD')

@login_required
def update_order_status(request, order_id):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        return redirect('home')
    order = get_object_or_404(Order, id=order_id, items__product__farmer=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = {'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED'}
        if new_status in valid:
            order.status = new_status
            if new_status == 'DELIVERED':
                if order.payment_method == 'ONLINE':
                    order.payment_status = 'PAID'
                award_reward_points(order)
                Notification.objects.create(user=order.customer, title='Order Delivered',
                                            message=f'Order {order.order_number} has been delivered.', notification_type='DELIVERY')
            if new_status == 'CANCELLED' and not order.stock_restored:
                for item in order.items.select_related('product'):
                    if item.product:
                        item.product.stock += item.quantity
                        item.product.is_available = True
                        item.product.save(update_fields=['stock', 'is_available'])
                order.stock_restored = True
            order.save()
            messages.success(request, 'Order status updated.')
    return redirect('farmer_orders')

@login_required
def rewards(request):
    profile = getattr(request.user, 'profile', None)
    return render(request, 'orders/rewards.html', {'points': getattr(profile, 'reward_points', 0),
                                                    'transactions': RewardTransaction.objects.filter(customer=request.user)})

@login_required
def request_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.status != 'DELIVERED':
        messages.error(request, 'Only delivered orders can be returned.')
        return redirect('order_detail', order_id=order.id)
    if ReturnRequest.objects.filter(order=order).exists():
        messages.warning(request, 'A return request already exists.')
        return redirect('order_detail', order_id=order.id)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if reason:
            ReturnRequest.objects.create(order=order, customer=request.user, reason=reason,
                                         refund_amount=order.total_amount,
                                         refund_method='ORIGINAL' if order.payment_method == 'ONLINE' else 'COD')
            Notification.objects.create(user=request.user, title='Return Request Submitted',
                                        message=f'Return request for {order.order_number} submitted.', notification_type='RETURN')
            messages.success(request, 'Return request submitted.')
            return redirect('order_detail', order_id=order.id)
        messages.error(request, 'Please enter a reason.')
    return render(request, 'orders/request_return.html', {'order': order})

@login_required
def notifications(request):
    qs = Notification.objects.filter(user=request.user)
    return render(request, 'orders/notifications.html', {'notifications': qs, 'unread_count': qs.filter(is_read=False).count()})

@login_required
def mark_notification_read(request, notification_id):
    n = get_object_or_404(Notification, id=notification_id, user=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return redirect('notifications')
