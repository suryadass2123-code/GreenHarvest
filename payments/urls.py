from django.urls import path
from .views import payment_page, payment_verify, payment_failed, payment_webhook

urlpatterns = [
    path('<int:order_id>/', payment_page, name='payment_page'),
    path('<int:order_id>/verify/', payment_verify, name='payment_verify'),
    path('<int:order_id>/failed/', payment_failed, name='payment_failed'),
    path('webhook/', payment_webhook, name='payment_webhook'),
]
