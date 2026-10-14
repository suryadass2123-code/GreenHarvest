from django.contrib.auth.models import User
from django.db import models
from orders.models import Order

class Payment(models.Model):
    STATUS_CHOICES = (('PENDING','Pending'), ('SUCCESS','Success'), ('FAILED','Failed'), ('REFUNDED','Refunded'))
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    razorpay_order_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    transaction_id = models.CharField(max_length=150, unique=True, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30, default='ONLINE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    gateway_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.order.order_number} - {self.status}'
