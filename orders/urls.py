from django.urls import path
from .views import *

urlpatterns = [
    path('cart/', cart_view, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/toggle/<int:product_id>/', wishlist_toggle, name='wishlist_toggle'),
    path('coupon/apply/', apply_coupon, name='apply_coupon'),
    path('coupon/remove/', remove_coupon, name='remove_coupon'),
    path('checkout/', checkout, name='checkout'),
    path('success/<int:order_id>/', order_success, name='order_success'),
    path('my-orders/', my_orders, name='my_orders'),
    path('my-orders/<int:order_id>/', order_detail, name='order_detail'),
    path('farmer/orders/', farmer_orders, name='farmer_orders'),
    path('farmer/orders/<int:order_id>/status/', update_order_status, name='update_order_status'),
    path('rewards/', rewards, name='rewards'),
    path('return/<int:order_id>/', request_return, name='request_return'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
]
