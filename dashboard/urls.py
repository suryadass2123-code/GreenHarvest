from django.urls import path
from .views import farmer_dashboard, customer_dashboard, admin_dashboard
urlpatterns = [
    path('farmer/', farmer_dashboard, name='farmer_dashboard'),
    path('customer/', customer_dashboard, name='customer_dashboard'),
    path('admin/', admin_dashboard, name='admin_dashboard'),
]
