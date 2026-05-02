import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from orders.models import Order

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    
def payment_completed(request):
    return render(request, 'payments/payment/completed.html')

def payment_canceled(request):
    return render(request, 'payments/payment/canceled.html')

def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    success_url = request.build_absolute_uri(reverse('payment:completed'))
    cancel_url = request.build_absolute_uri(reverse('payment:canceled'))

    session_data = {
        'mode': 'payment',
        'client_reference_id': order.id,
        'success_url': success_url,
        'cancel_url': cancel_url,
        'line_items': []
    }

    for item in order.items.all():
        session_data['line_items'].append({
            'price_data': {
                'unit_amount': int(item.price * 100),
                'currency': 'uah',
                'product_data': {'name': item.product.name},
            },
            'quantity': item.quantity,
        })

    # Створюємо сесію Stripe
    session = stripe.checkout.Session.create(**session_data)
    return redirect(session.url, code=303)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session.mode == 'payment' and session.payment_status == 'paid':
            try:
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)
            order.paid = True
            order.save()

    return HttpResponse(status=200)