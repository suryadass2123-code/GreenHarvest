from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from products.models import Product
from orders.models import Order
from .forms import ReviewForm
from .models import Review

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if Review.objects.filter(product=product, customer=request.user).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect('product_detail', product_id=product.id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.customer = request.user
            review.order = Order.objects.filter(customer=request.user, status='DELIVERED', items__product=product).first()
            review.save()
            messages.success(request, 'Your review was submitted.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()
    return render(request, 'reviews/add_review.html', {'form': form, 'product': product})

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, customer=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review updated.')
            return redirect('product_detail', product_id=review.product.id)
    else:
        form = ReviewForm(instance=review)
    return render(request, 'reviews/add_review.html', {'form': form, 'product': review.product, 'edit_mode': True})

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, customer=request.user)
    pid = review.product.id
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
    return redirect('product_detail', product_id=pid)
