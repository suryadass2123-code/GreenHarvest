import json
import hmac
import hashlib
from decimal import Decimal
import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from orders.models import Notification, Order
from .models import Payment


def get_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.payment_method != 'ONLINE':
        messages.info(request, 'This order uses Cash on Delivery.')
        return redirect('order_detail', order_id=order.id)
    client = get_client()
    if not client:
        return render(request, 'payments/payment_page.html', {'order': order, 'payment': None, 'gateway_configured': False})
    amount_paise = int(Decimal(order.total_amount) * 100)
    payment, _ = Payment.objects.get_or_create(order=order, defaults={
        'customer': request.user, 'amount': order.total_amount, 'payment_method': 'ONLINE', 'status': 'PENDING'
    })
    if not payment.razorpay_order_id:
        rz_order = client.order.create({'amount': amount_paise, 'currency': 'INR', 'receipt': order.order_number, 'notes': {'customer': request.user.username}})
        payment.razorpay_order_id = rz_order['id']
        payment.gateway_response = json.dumps(rz_order)
        payment.save(update_fields=['razorpay_order_id', 'gateway_response', 'updated_at'])
    return render(request, 'payments/payment_page.html', {
        'order': order, 'payment': payment, 'gateway_configured': True,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount_paise': amount_paise,
    })

@login_required
def payment_verify(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'POST required.'}, status=405)
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    payment = get_object_or_404(Payment, order=order)
    client = get_client()
    if not client or not payment.razorpay_order_id:
        return JsonResponse({'ok': False, 'message': 'Payment gateway is not configured.'}, status=400)
    data = {
        'razorpay_payment_id': request.POST.get('razorpay_payment_id', ''),
        'razorpay_order_id': request.POST.get('razorpay_order_id', ''),
        'razorpay_signature': request.POST.get('razorpay_signature', ''),
    }
    try:
        client.utility.verify_payment_signature(data)
    except razorpay.errors.SignatureVerificationError:
        payment.status = 'FAILED'
        payment.gateway_response = 'Signature verification failed.'
        payment.save(update_fields=['status', 'gateway_response', 'updated_at'])
        return JsonResponse({'ok': False, 'message': 'Payment verification failed.'}, status=400)
    payment.transaction_id = data['razorpay_payment_id']
    payment.status = 'SUCCESS'
    payment.gateway_response = json.dumps(data)
    payment.save(update_fields=['transaction_id', 'status', 'gateway_response', 'updated_at'])
    order.payment_status = 'PAID'
    order.status = 'CONFIRMED'
    order.save(update_fields=['payment_status', 'status', 'updated_at'])
    Notification.objects.create(user=request.user, title='Payment Successful',
                                message=f'Payment received for {order.order_number}.', notification_type='PAYMENT')
    return JsonResponse({'ok': True, 'redirect_url': f'/orders/success/{order.id}/'})

@login_required
def payment_failed(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    payment = get_object_or_404(Payment, order=order)
    payment.status = 'FAILED'
    payment.save(update_fields=['status', 'updated_at'])
    messages.error(request, 'Payment failed. You can retry the payment from the order page.')
    return redirect('order_detail', order_id=order.id)

@csrf_exempt
def payment_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    signature = request.headers.get('X-Razorpay-Signature', '')
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    body = request.body
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest() if secret else ''
    if not secret or not hmac.compare_digest(expected, signature):
        return HttpResponse('Invalid signature', status=400)
    payload = json.loads(body.decode('utf-8'))
    event = payload.get('event', '')
    if event == 'payment.captured':
        entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        rz_order_id = entity.get('order_id')
        payment_id = entity.get('id')
        payment = Payment.objects.filter(razorpay_order_id=rz_order_id).select_related('order').first()
        if payment:
            payment.status = 'SUCCESS'
            payment.transaction_id = payment_id
            payment.save(update_fields=['status', 'transaction_id', 'updated_at'])
            payment.order.payment_status = 'PAID'
            payment.order.status = 'CONFIRMED'
            payment.order.save(update_fields=['payment_status', 'status', 'updated_at'])
    return HttpResponse('OK')
