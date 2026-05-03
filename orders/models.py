from django.db import models
from products.models import Product
from django.utils import timezone

class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    coupon = models.ForeignKey("Coupon", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    discount = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Замовлення {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount_amount(self):
        total = self.get_total_cost()
        return (total * self.discount) / 100

    def get_total_after_discount(self):
        return self.get_total_cost() - self.get_discount_amount()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.PositiveSmallIntegerField(help_text="Знижка у відсотках")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to