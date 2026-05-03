from django.shortcuts import render, redirect
from django.urls import reverse 
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.conf import settings
from django.core.mail import send_mail
import requests

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            coupon = cart.get_coupon()
            if coupon and coupon.is_valid():
                order.coupon = coupon
                order.discount = coupon.discount
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                        product=item['product'],
                                        price=item['price'],
                                        quantity=item['quantity'])
            _send_order_notifications(order)
            cart.clear()
            
            request.session['order_id'] = order.id
            
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
        send_mail(
            subject=f"Підтвердження замовлення #{order.id}",
            message=customer_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[order.email],
            fail_silently=True,
        )

    admin_email = getattr(settings, "ORDER_ADMIN_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if admin_email:
        send_mail(
            subject=f"Нове замовлення #{order.id}",
            message=f"Нове замовлення на суму {total} грн від {order.first_name} {order.last_name}.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[admin_email],
            fail_silently=True,
        )

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
            pass