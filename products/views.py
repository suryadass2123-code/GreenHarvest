from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CategoryForm, ProductForm
from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(is_available=True, stock__gt=0).select_related('category', 'farmer')
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))
    if category_id.isdigit():
        products = products.filter(category_id=int(category_id))
    categories = Category.objects.all().order_by('name')
    products = list(products.order_by('-created_at'))
    for p in products:
        p.avg_rating = p.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg'] or 0
    return render(request, 'products/product_list.html', {'products': products, 'categories': categories, 'q': q, 'selected_category': category_id})


def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.select_related('category', 'farmer'), id=product_id)
    reviews = product.reviews.filter(is_approved=True).select_related('customer')
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    return render(request, 'products/product_detail.html', {'product': product, 'reviews': reviews, 'average_rating': round(average_rating, 1), 'review_count': reviews.count()})

@login_required
def farmer_products(request):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        messages.error(request, 'Only farmers can access this page.')
        return redirect('home')
    products = Product.objects.filter(farmer=request.user).select_related('category').order_by('-created_at')
    return render(request, 'products/farmer_products.html', {'products': products})

@login_required
def product_create(request):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        return redirect('home')
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.farmer = request.user
        product.save()
        messages.success(request, 'Product added successfully.')
        return redirect('farmer_products')
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Add Product'})

@login_required
def product_edit(request, product_id):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        return redirect('home')
    product = get_object_or_404(Product, id=product_id, farmer=request.user)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('farmer_products')
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})

@login_required
def product_delete(request, product_id):
    if getattr(request.user.profile, 'role', '') != 'farmer':
        return redirect('home')
    product = get_object_or_404(Product, id=product_id, farmer=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('farmer_products')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
