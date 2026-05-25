from django.db import models
from django.conf import settings
from products.models import Product
from django.utils import timezone

from decimal import Decimal

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250, blank=True, null=True)
    delivery_service = models.CharField(
        max_length=50,
        choices=[
            ('nova_poshta', 'Нова пошта'),
            ('ukr_poshta', 'Укр пошта'),
            ('meest', 'Meest')
        ],
        default='nova_poshta'
    )
    city = models.CharField(max_length=100, blank=True)
    branch = models.CharField(max_length=250, blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('card', 'Оплата карткою'),
            ('cod', 'Накладений платіж'),
            ('partial', 'Внесок 10% від вартості товару')
        ],
        default='card',
        verbose_name="Спосіб оплати"
    )
    created = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ('pending', 'Очікує оплати'),
        ('paid', 'Оплачено'),
        ('shipped', 'Надіслано'),
        ('delivered', 'Доставлено'),
        ('canceled', 'Скасовано'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    coupon = models.ForeignKey("Coupon", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    discount = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Замовлення {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount_amount(self):
        total = self.get_total_cost()
        if self.coupon:
            if getattr(self.coupon, 'discount_type', 'percentage') == 'percentage':
                return (total * self.discount) / 100
            else:  # 'fixed'
                return min(getattr(self.coupon, 'discount_value', Decimal("0.00")), total)
        return (total * self.discount) / Decimal("100")

    def get_total_after_discount(self):
        return self.get_total_cost() - self.get_discount_amount()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            if self.status == 'canceled':
                self.sub_orders.update(status='canceled')
            elif self.status == 'paid':
                self.sub_orders.filter(status='pending').update(status='paid')

class SubOrder(models.Model):
    order = models.ForeignKey(Order, related_name='sub_orders', on_delete=models.CASCADE)
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sub_orders', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Очікує оплати'),
            ('paid', 'Оплачено'),
            ('shipped', 'Надіслано'),
            ('delivered', 'Доставлено'),
            ('canceled', 'Скасовано'),
        ],
        default='pending',
    )
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    waybill_ref = models.CharField(max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'SubOrder #{self.id} for Order #{self.order.id} (Vendor: {self.vendor.username})'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount_amount(self):
        order_total = self.order.get_total_cost()
        if order_total > 0:
            share = self.get_total_cost() / order_total
            return self.order.get_discount_amount() * share
        return Decimal("0.00")

    def get_total_after_discount(self):
        return self.get_total_cost() - self.get_discount_amount()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    sub_order = models.ForeignKey(SubOrder, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.PositiveSmallIntegerField(default=0, help_text="Знижка у відсотках (для відсоткового типу)")
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Відсоток'),
            ('fixed', 'Фіксована сума')
        ],
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Значення знижки (в грн для фіксованої знижки)"
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to