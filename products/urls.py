
from django.urls import path

from .views import (
    home,
    product_list,
    product_detail,
    farmer_products,
    product_create,
    product_edit,
    product_delete,
)

urlpatterns = [
    # Main GreenHarvest homepage
    path('', home, name='home'),

    # Product listing page
    path('products/', product_list, name='product_list'),

    # Product details
    path(
        'products/<int:product_id>/',
        product_detail,
        name='product_detail',
    ),

    # Farmer product management
    path('farmer/products/', farmer_products, name='farmer_products'),

    path(
        'farmer/products/add/',
        product_create,
        name='product_create',
    ),

    path(
        'farmer/products/<int:product_id>/edit/',
        product_edit,
        name='product_edit',
    ),

    path(
        'farmer/products/<int:product_id>/delete/',
        product_delete,
        name='product_delete',
    ),
]
