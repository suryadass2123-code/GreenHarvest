from django.db.models import Avg
from django.shortcuts import render
from products.models import Category, Product


def home(request):
    categories = Category.objects.all().order_by('name')[:8]
    featured_products = (
        Product.objects.filter(is_available=True, stock__gt=0)
        .select_related('category', 'farmer')
        .order_by('-created_at')[:8]
    )
    for product in featured_products:
        product.avg_rating = product.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg'] or 0
    return render(request, 'home.html', {
        'categories': categories,
        'featured_products': featured_products,
    })
