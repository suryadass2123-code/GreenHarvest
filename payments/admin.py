from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'customer', 'amount', 'payment_method', 'status', 'razorpay_order_id', 'transaction_id', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('order__order_number', 'customer__username', 'razorpay_order_id', 'transaction_id')
