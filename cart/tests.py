from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product


class CartDiscountTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            category=category,
            name="Phone",
            slug="phone",
            price="100.00",
            discount_percent=20,
            available=True,
        )

    def test_cart_uses_discounted_price(self):
        self.client.post(reverse("cart:cart_add", args=[self.product.id]))
        response = self.client.get(reverse("cart:cart_detail"))
        item = list(response.context["cart"])[0]

        self.assertEqual(str(item["price"]), "80.00")
