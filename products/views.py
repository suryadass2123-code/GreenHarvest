
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm
from .models import Category, Product


# Main GreenHarvest homepage
def home(request):
    categories = Category.objects.all().order_by('name')

    featured_products = list(
        Product.objects
        .filter(is_available=True, stock__gt=0)
        .select_related('category', 'farmer')
        .order_by('-created_at')[:4]
    )

    for product in featured_products:
        product.avg_rating = (
            product.reviews
            .filter(is_approved=True)
            .aggregate(avg=Avg('rating'))['avg'] or 0
        )

    context = {
        'categories': categories,
        'featured_products': featured_products,
    }

    return render(request, 'home.html', context)


# Product listing page
def product_list(request):
    products = (
        Product.objects
        .filter(is_available=True, stock__gt=0)
        .select_related('category', 'farmer')
    )

    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(location__icontains=q)
        )

    if category_id.isdigit():
        products = products.filter(category_id=int(category_id))

    categories = Category.objects.all().order_by('name')
    products = list(products.order_by('-created_at'))

    for product in products:
        product.avg_rating = (
            product.reviews
            .filter(is_approved=True)
            .aggregate(avg=Avg('rating'))['avg'] or 0
        )

    context = {
        'products': products,
        'categories': categories,
        'q': q,
        'selected_category': category_id,
    }

    return render(
        request,
        'products/product_list.html',
        context,
    )


# Product details page
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'farmer'),
        id=product_id,
    )

    reviews = product.reviews.filter(
        is_approved=True
    ).select_related('customer')

    average_rating = (
        reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    )

    context = {
        'product': product,
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'review_count': reviews.count(),
    }

    return render(
        request,
        'products/product_detail.html',
        context,
    )


# Farmer's products
@login_required
def farmer_products(request):
    profile = getattr(request.user, 'profile', None)

    if getattr(profile, 'role', '').lower() != 'farmer':
        messages.error(
            request,
            'Only farmers can access this page.',
        )
        return redirect('home')

    products = (
        Product.objects
        .filter(farmer=request.user)
        .select_related('category')
        .order_by('-created_at')
    )

    return render(
        request,
        'products/farmer_products.html',
        {'products': products},
    )


# Add a product
@login_required
def product_create(request):
    profile = getattr(request.user, 'profile', None)

    if getattr(profile, 'role', '').lower() != 'farmer':
        messages.error(
            request,
            'Only farmers can add products.',
        )
        return redirect('home')

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.farmer = request.user
        product.save()

        messages.success(
            request,
            'Product added successfully.',
        )
        return redirect('farmer_products')

    return render(
        request,
        'products/product_form.html',
        {
            'form': form,
            'title': 'Add Product',
        },
    )


# Edit a product
@login_required
def product_edit(request, product_id):
    profile = getattr(request.user, 'profile', None)

    if getattr(profile, 'role', '').lower() != 'farmer':
        messages.error(
            request,
            'Only farmers can edit products.',
        )
        return redirect('home')

    product = get_object_or_404(
        Product,
        id=product_id,
        farmer=request.user,
    )

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
        instance=product,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()

        messages.success(
            request,
            'Product updated successfully.',
        )
        return redirect('farmer_products')

    return render(
        request,
        'products/product_form.html',
        {
            'form': form,
            'title': 'Edit Product',
            'product': product,
        },
    )


# Delete a product
@login_required
def product_delete(request, product_id):
    profile = getattr(request.user, 'profile', None)

    if getattr(profile, 'role', '').lower() != 'farmer':
        messages.error(
            request,
            'Only farmers can delete products.',
        )
        return redirect('home')

    product = get_object_or_404(
        Product,
        id=product_id,
        farmer=request.user,
    )

    if request.method == 'POST':
        product.delete()

        messages.success(
            request,
            'Product deleted successfully.',
        )
        return redirect('farmer_products')

    return render(
        request,
        'products/product_confirm_delete.html',
        {'product': product},
    )
