import logging

from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse 
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.conf import settings
from django.core.mail import send_mail
import requests

logger = logging.getLogger(__name__)


def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                coupon = cart.get_coupon()
                if coupon and coupon.is_valid():
                    order.coupon = coupon
                    order.discount = coupon.discount
                order.save()
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        price=item['price'],
                        quantity=item['quantity'],
                    )
            
            request.session['order_id'] = order.id
            _send_order_notifications(order)
            cart.clear()
            
            return redirect(reverse('payment:process'))
            
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})


def _send_order_notifications(order):
    total = order.get_total_after_discount()
    customer_message = (
        f"Дякуємо за замовлення #{order.id}!\n"
        f"Сума: {total} грн.\n"
        "Ми обробляємо ваше замовлення."
    )
    if order.email:
        try:
            send_mail(
                subject=f"Підтвердження замовлення #{order.id}",
                message=customer_message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[order.email],
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send order confirmation email for order %s", order.id)

    admin_email = getattr(settings, "ORDER_ADMIN_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if admin_email:
        try:
            send_mail(
                subject=f"Нове замовлення #{order.id}",
                message=f"Нове замовлення на суму {total} грн від {order.first_name} {order.last_name}.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[admin_email],
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send admin order notification for order %s", order.id)

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
    if bot_token and chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Нове замовлення #{order.id}\nСума: {total} грн\nКлієнт: {order.first_name} {order.last_name}",
                },
                timeout=5,
            )
        except requests.RequestException:
            logger.warning("Failed to send telegram notification for order %s", order.id)