import logging
import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Order

logger = logging.getLogger(__name__)

@shared_task
def send_order_notifications_task(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error("Order %s does not exist, cannot send notifications.", order_id)
        return

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
