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

    payment_method = getattr(order, 'payment_method', 'card')
    if payment_method == 'cod':
        return redirect('payment:completed')

    success_url = request.build_absolute_uri(reverse('payment:completed'))
    cancel_url = request.build_absolute_uri(reverse('payment:canceled'))

    from decimal import Decimal

    line_items = []
    if payment_method == 'partial':
        total_after_discount = order.get_total_after_discount()
        downpayment_amount = (total_after_discount * Decimal("0.10")).quantize(Decimal("0.01"))
        line_items.append({
            'price_data': {
                'unit_amount': int(downpayment_amount * 100),
                'currency': 'uah',
                'product_data': {
                    'name': f'Передплата 10% за замовлення #{order.id}',
                },
            },
            'quantity': 1,
        })
    else:
        total_cost = order.get_total_cost()
        discount_amount = order.get_discount_amount()
        discount_ratio = (discount_amount / total_cost) if total_cost > 0 else Decimal("0.00")
        discount_multiplier = Decimal("1") - discount_ratio
        for item in order.items.all():
            discounted_price = (item.price * discount_multiplier).quantize(Decimal("0.01"))
            line_items.append({
                'price_data': {
                    'unit_amount': int(discounted_price * 100),
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

            updated = Order.objects.filter(id=order_id, paid=False).update(paid=True, status='paid')
            if updated:
                from decimal import Decimal
                from orders.models import SubOrder
                SubOrder.objects.filter(order_id=order_id).update(status='paid')
                
                sub_orders = SubOrder.objects.filter(order_id=order_id).select_related('vendor', 'vendor__seller_profile')
                for sub_order in sub_orders:
                    profile = getattr(sub_order.vendor, 'seller_profile', None)
                    if profile and profile.stripe_account_id:
                        vendor_total_after_discount = sub_order.get_total_after_discount()
                        commission = vendor_total_after_discount * Decimal("0.10")
                        payout_amount = vendor_total_after_discount - commission
                        if payout_amount > 0:
                            payout_cents = int(payout_amount * 100)
                            try:
                                stripe.Transfer.create(
                                    amount=payout_cents,
                                    currency="uah",
                                    destination=profile.stripe_account_id,
                                    transfer_group=f"order_{order_id}",
                                    description=f"Transfer for SubOrder #{sub_order.id}"
                                )
                                logger.info("Stripe Transfer created successfully for SubOrder %s to account %s", sub_order.id, profile.stripe_account_id)
                            except Exception as e:
                                logger.exception("Stripe Transfer failed for SubOrder %s: %s", sub_order.id, e)
                    else:
                        logger.warning("Vendor %s has no stripe_account_id configured. Payout of %s pending.", sub_order.vendor.username, sub_order.get_total_after_discount())
            elif not Order.objects.filter(id=order_id).exists():
                logger.warning("Order not found for Stripe session: %s", order_id)
                return HttpResponse(status=404)

    return HttpResponse(status=200)