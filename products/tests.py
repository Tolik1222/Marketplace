from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product


class ProductAddAccessTests(TestCase):
    def setUp(self):
        self.url = reverse("products:product_add")
        self.user_model = get_user_model()

    def test_product_add_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_product_add_forbidden_for_non_staff(self):
        user = self.user_model.objects.create_user(username="buyer", password="pass12345")
        self.client.login(username="buyer", password="pass12345")

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("products:product_list"))

    def test_product_add_sets_owner_for_staff(self):
        category = Category.objects.create(name="Cat", slug="cat")
        staff = self.user_model.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")

        response = self.client.post(
            self.url,
            {
                "category": category.id,
                "name": "Created by staff",
                "description": "desc",
                "price": "199.99",
                "discount_percent": 0,
                "available": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name="Created by staff")
        self.assertEqual(product.owner, staff)


class ProductListFilterSortTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Electronics", slug="electronics")
        Product.objects.create(
            category=category,
            name="Phone",
            slug="phone",
            price="100.00",
            description="Budget phone",
            available=True,
        )
        Product.objects.create(
            category=category,
            name="Laptop",
            slug="laptop",
            price="1000.00",
            description="Work laptop",
            available=True,
        )
        Product.objects.create(
            category=category,
            name="Camera",
            slug="camera",
            price="500.00",
            description="Out of stock camera",
            available=False,
        )

    def test_filters_by_price_range(self):
        response = self.client.get(reverse("products:product_list"), {"price_min": "50", "price_max": "600"})
        products = list(response.context["products"])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Phone")

    def test_sorts_by_price_ascending(self):
        response = self.client.get(reverse("products:product_list"), {"sort": "price_asc"})
        products = list(response.context["products"])
        self.assertEqual(products[0].name, "Phone")
        self.assertEqual(products[-1].name, "Laptop")

    def test_discounted_products_context_contains_sales(self):
        sale_product = Product.objects.get(slug="phone")
        sale_product.discount_percent = 20
        sale_product.save(update_fields=["discount_percent"])

        response = self.client.get(reverse("products:product_list"))
        discounted_products = list(response.context["discounted_products"])

        self.assertEqual(len(discounted_products), 1)
        self.assertEqual(discounted_products[0].slug, "phone")

    def test_product_get_discounted_price(self):
        sale_product = Product.objects.get(slug="phone")
        sale_product.discount_percent = 25

        self.assertEqual(sale_product.get_discounted_price(), Decimal("75.00"))
