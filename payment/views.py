import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from orders.models import Order

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

    
def payment_completed(request):
    return render(request, 'payments/payment/completed.html')

def payment_canceled(request):
    return render(request, 'payments/payment/canceled.html')

def payment_process(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'Не знайдено активного замовлення для оплати.')
        return redirect('cart:cart_detail')

    order = get_object_or_404(Order, id=order_id)
    if order.paid:
        messages.info(request, "Це замовлення вже оплачене.")
        return redirect("payment:completed")

    success_url = request.build_absolute_uri(reverse('payment:completed'))
    cancel_url = request.build_absolute_uri(reverse('payment:canceled'))

    line_items = []
    for item in order.items.all():
        line_items.append({
            'price_data': {
                'unit_amount': int(item.price * 100),
                'currency': 'uah',
                'product_data': {'name': item.product.name},
            },
            'quantity': item.quantity,
        })

    if not line_items:
        messages.error(request, 'Замовлення не містить товарів. Додайте товари в кошик і спробуйте знову.')
        return redirect('cart:cart_detail')

    session_data = {
        'mode': 'payment',
        'client_reference_id': order.id,
        'success_url': success_url,
        'cancel_url': cancel_url,
        'line_items': line_items,
    }

    try:
        session = stripe.checkout.Session.create(**session_data)
    except stripe.error.StripeError:
        logger.exception("Stripe checkout session creation failed for order %s", order.id)
        messages.error(request, "Не вдалося створити платіжну сесію. Спробуйте ще раз.")
        return redirect("cart:cart_detail")

    return redirect(session.url, code=303)


@csrf_exempt
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured")
        return HttpResponse(status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.warning("Invalid Stripe webhook payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        mode = getattr(session, "mode", None) or session.get("mode")
        payment_status = getattr(session, "payment_status", None) or session.get("payment_status")
        client_reference_id = getattr(session, "client_reference_id", None) or session.get("client_reference_id")

        if mode == 'payment' and payment_status == 'paid':
            try:
                order_id = int(client_reference_id)
            except (TypeError, ValueError):
                logger.warning("Invalid client_reference_id in Stripe session: %s", client_reference_id)
                return HttpResponse(status=400)

            updated = Order.objects.filter(id=order_id, paid=False).update(paid=True)
            if not updated and not Order.objects.filter(id=order_id).exists():
                logger.warning("Order not found for Stripe session: %s", order_id)
                return HttpResponse(status=404)

    return HttpResponse(status=200)