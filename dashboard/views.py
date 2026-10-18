
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth, TruncDate
from django.shortcuts import render
from django.utils import timezone

from accounts.models import Profile
from orders.models import Order, OrderItem
from products.models import Product


def get_user_role(user):
    """Return the user's profile role safely."""
    try:
        return user.profile.role
    except (Profile.DoesNotExist, AttributeError):
        return ''


@login_required
def farmer_dashboard(request):
    if get_user_role(request.user) != 'farmer':
        return render(request, 'dashboard/access_denied.html')

    products = (
        Product.objects
        .filter(farmer=request.user)
        .select_related('category')
        .order_by('-created_at')
    )

    farmer_orders = (
        Order.objects
        .filter(items__product__farmer=request.user)
        .distinct()
        .select_related('customer')
        .order_by('-created_at')
    )

    pending_count = farmer_orders.filter(status='PENDING').count()
    delivered_count = farmer_orders.filter(status='DELIVERED').count()

    revenue = (
        OrderItem.objects
        .filter(
            product__farmer=request.user,
            order__status='DELIVERED',
        )
        .aggregate(total=Sum(F('price') * F('quantity')))
        .get('total')
        or Decimal('0.00')
    )

    today = timezone.localdate()
    start_day = today - timedelta(days=6)

    daily_rows = (
        OrderItem.objects
        .filter(
            product__farmer=request.user,
            order__status='DELIVERED',
            order__created_at__date__gte=start_day,
            order__created_at__date__lte=today,
        )
        .annotate(day=TruncDate('order__created_at'))
        .values('day')
        .annotate(total=Sum(F('price') * F('quantity')))
        .order_by('day')
    )

    daily_lookup = {
        row['day']: float(row['total'] or 0)
        for row in daily_rows
        if row['day']
    }

    sales_labels = []
    sales_values = []

    for offset in range(7):
        current_day = start_day + timedelta(days=offset)
        sales_labels.append(current_day.strftime('%a'))
        sales_values.append(daily_lookup.get(current_day, 0))

    top_products = (
        OrderItem.objects
        .filter(
            product__farmer=request.user,
            order__status='DELIVERED',
        )
        .values('product_name')
        .annotate(
            total_quantity=Sum('quantity'),
            revenue=Sum(F('price') * F('quantity')),
        )
        .order_by('-total_quantity')[:5]
    )

    context = {
        'product_count': products.count(),
        'active_product_count': products.filter(
            is_available=True,
            stock__gt=0,
        ).count(),
        'order_count': farmer_orders.count(),
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'revenue': revenue,
        'products': products[:4],
        'top_products': top_products,
        'recent_orders': farmer_orders[:6],
        'sales_labels': sales_labels,
        'sales_values': sales_values,
    }

    return render(
        request,
        'dashboard/farmer_dashboard.html',
        context,
    )


@login_required
def customer_dashboard(request):
    if get_user_role(request.user) != 'customer':
        return render(request, 'dashboard/access_denied.html')

    orders = (
        Order.objects
        .filter(customer=request.user)
        .order_by('-created_at')
    )

    context = {
        'order_count': orders.count(),
        'orders': orders[:5],
    }

    return render(
        request,
        'dashboard/customer_dashboard.html',
        context,
    )


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

    low_stock_products = Product.objects.filter(
        stock__lte=10,
        is_available=True,
    ).count()

    total_revenue = (
        Order.objects
        .filter(status='DELIVERED')
        .aggregate(total=Sum('total_amount'))['total']
        or Decimal('0.00')
    )

    today = timezone.localdate()
    current_month = today.replace(day=1)

    months = []

    for offset in range(5, -1, -1):
        month_index = (
            current_month.year * 12
            + current_month.month - 1
            - offset
        )
        months.append(
            date(
                month_index // 12,
                month_index % 12 + 1,
                1,
            )
        )

    monthly_rows = (
        Order.objects
        .filter(
            status='DELIVERED',
            created_at__date__gte=months[0],
            created_at__date__lte=today,
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(revenue=Sum('total_amount'))
        .order_by('month')
    )

    monthly_lookup = {
        row['month'].date().replace(day=1): float(row['revenue'] or 0)
        for row in monthly_rows
        if row['month']
    }

    monthly_labels = [month.strftime('%b %Y') for month in months]
    monthly_revenue = [
        monthly_lookup.get(month, 0)
        for month in months
    ]

    status_rows = (
        Order.objects
        .values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )

    status_labels = [
        row['status'].title()
        for row in status_rows
    ]
    status_counts = [
        row['total']
        for row in status_rows
    ]

    top_customers = (
        Order.objects
        .filter(status='DELIVERED')
        .values(
            'customer__username',
            'customer__first_name',
            'customer__last_name',
        )
        .annotate(
            order_count=Count('id'),
            total_spent=Sum('total_amount'),
        )
        .order_by('-total_spent')[:5]
    )

    top_products = (
        OrderItem.objects
        .filter(order__status='DELIVERED')
        .values('product_name')
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity')),
        )
        .order_by('-total_quantity')[:5]
    )

    low_stock_list = (
        Product.objects
        .filter(stock__lte=10, is_available=True)
        .select_related('category', 'farmer')
        .order_by('stock')[:10]
    )

    recent_orders = (
        Order.objects
        .select_related('customer')
        .order_by('-created_at')[:8]
    )

    context = {
        'total_customers': total_customers,
        'total_farmers': total_farmers,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'low_stock_products': low_stock_products,
        'total_revenue': total_revenue,
        'months': months,
        'monthly_labels': monthly_labels,
        'monthly_revenue': monthly_revenue,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'top_customers': top_customers,
        'top_products': top_products,
        'low_stock_list': low_stock_list,
        'recent_orders': recent_orders,
    }

    return render(
        request,
        'dashboard/admin_dashboard.html',
        context,
    )
