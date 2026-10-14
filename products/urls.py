from django.urls import path
from .views import product_list, product_detail, farmer_products, product_create, product_edit, product_delete

urlpatterns = [
    path('', product_list, name='product_list'),
    path('<int:product_id>/', product_detail, name='product_detail'),
    path('farmer/', farmer_products, name='farmer_products'),
    path('farmer/add/', product_create, name='product_create'),
    path('farmer/<int:product_id>/edit/', product_edit, name='product_edit'),
    path('farmer/<int:product_id>/delete/', product_delete, name='product_delete'),
]
