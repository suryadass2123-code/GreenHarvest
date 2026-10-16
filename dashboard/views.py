from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from accounts.models import Profile
from orders.models import Order, OrderItem
from products.models import Product


@login_required
def farmer_dashboard(request):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        return render(request, 'dashboard/access_denied.html')

    products = Product.objects.filter(farmer=request.user).select_related('category').order_by('-created_at')
    farmer_order_ids = list(
        Order.objects.filter(items__product__farmer=request.user)
        .values_list('id', flat=True)
        .distinct()
    )
    farmer_orders = Order.objects.filter(id__in=farmer_order_ids)

    pending_count = farmer_orders.filter(status='PENDING').count()
    delivered_count = farmer_orders.filter(status='DELIVERED').count()

    revenue = (
        OrderItem.objects.filter(
            product__farmer=request.user,
            order__status='DELIVERED',
        ).aggregate(total=Sum(F('price') * F('quantity')))
        .get('total')
        or Decimal('0.00')
    )

    # Last 7 days of farmer sales (based on delivered order items).
    today = timezone.localdate()
    start_day = today - timedelta(days=6)
    daily_rows = (
        OrderItem.objects.filter(
            product__farmer=request.user,
            order__status='DELIVERED',
            order__created_at__date__gte=start_day,
        )
        .annotate(day=TruncDate('order__created_at'))
        .values('day')
        .annotate(total=Sum(F('price') * F('quantity')))
        .order_by('day')
    )
    daily_lookup = {row['day']: float(row['total'] or 0) for row in daily_rows if row['day']}
    sales_labels = []
    sales_values = []
    for offset in range(7):
        d = start_day + timedelta(days=offset)
        sales_labels.append(d.strftime('%a'))
        sales_values.append(daily_lookup.get(d, 0))

    
    top_products = (
        OrderItem.objects
        .filter(
            product__farmer=request.user,
            order__status='DELIVERED'
        )
        .values('product_name')
        .annotate(
            total_quantity=Sum('quantity'),
            revenue=Sum(F('price') * F('quantity'))
        )
        .order_by('-total_quantity')[:5]
    )

    recent_orders = farmer_orders.select_related('customer').order_by('-created_at')[:6]


    context = {
        'product_count': products.count(),
        'active_product_count': products.filter(is_available=True, stock__gt=0).count(),
        'order_count': farmer_orders.count(),
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'revenue': revenue,
        'products': products[:4],
        'top_products': top_products,
        'recent_orders': recent_orders,
        'sales_labels': sales_labels,
        'sales_values': sales_values,
    }
    return render(request, 'dashboard/farmer_dashboard.html', context)


@login_required
def customer_dashboard(request):
    if getattr(request.user.profile, 'role', '') != 'customer':
        return render(request, 'dashboard/access_denied.html')
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'dashboard/customer_dashboard.html', {
        'order_count': orders.count(),
        'orders': orders[:5],
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return render(request, 'dashboard/access_denied.html')

    total_customers = Profile.objects.filter(role='customer').count()
    total_farmers = Profile.objects.filter(role='farmer').count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='PENDING').count()
    delivered_orders = Order.objects.filter(status='DELIVERED').count()
    low_stock_products = Product.objects.filter(stock__lte=10, is_available=True).count()
    total_revenue = Order.objects.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or 0

    today = timezone.localdate()
    current_month = date(today.year, today.month, 1)
    months = []
    for i in range(5, -1, -1):
        index = current_month.year * 12 + current_month.month - 1 - i
        months.append(date(index // 12, index % 12 + 1, 1))

    monthly = (
        Order.objects.filter(status='DELIVERED', created_at__date__gte=months[0])
        .annotate(month=TruncDate('created_at'))
        .values('month')
        .annotate(revenue=Sum('total_amount'))
        .order_by('month')
    )
    monthly_labels = [m.strftime('%b %Y') for m in months]
    monthly_lookup = {}
    # Grouping by exact day is sufficient for small demo data; aggregate in Python by month.
    for row in monthly:
        if row['month']:
            m = row['month'].replace(day=1)
            monthly_lookup[m] = monthly_lookup.get(m, 0) + float(row['revenue'] or 0)
    monthly_revenue = [monthly_lookup.get(m, 0) for m in months]

    status_rows = Order.objects.values('status').annotate(total=Count('id')).order_by('status')
    status_labels = [r['status'].title() for r in status_rows]
    status_counts = [r['total'] for r in status_rows]

    top_customers = (
        Order.objects.filter(status='DELIVERED')
        .values('customer__username', 'customer__first_name', 'customer__last_name')
        .annotate(order_count=Count('id'), total_spent=Sum('total_amount'))
        .order_by('-total_spent')[:5]
    )

    top_products = (
        OrderItem.objects.filter(order__status='DELIVERED')
        .values('product_name')
        .annotate(total_quantity=Sum('quantity'), total_revenue=Sum(F('price') * F('quantity')))
        .order_by('-total_quantity')[:5]
    )
    low_stock_list = Product.objects.filter(stock__lte=10, is_available=True).select_related('category', 'farmer').order_by('stock')[:10]
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:8]

    return render(request, 'dashboard/admin_dashboard.html', locals())
