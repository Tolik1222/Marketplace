from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order


class ProfileOrderHistoryTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="testuser",
            password="pass12345",
            email="buyer@example.com",
        )
        self.other_user = self.user_model.objects.create_user(
            username="other",
            password="pass12345",
            email="other@example.com",
        )

    def test_profile_shows_order_by_user_link(self):
        own_order = Order.objects.create(
            user=self.user,
            first_name="Buyer",
            last_name="User",
            email="another@email.com",
            address="Kyiv",
            paid=True,
        )
        Order.objects.create(
            user=self.other_user,
            first_name="Other",
            last_name="User",
            email=self.user.email,
            address="Lviv",
            paid=False,
        )

        self.client.login(username="testuser", password="pass12345")
        response = self.client.get(reverse("accounts:profile"))
        orders = list(response.context["user_orders"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, own_order.id)

    def test_profile_shows_legacy_orders_by_email(self):
        own_order = Order.objects.create(
            first_name="Buyer",
            last_name="User",
            email=self.user.email,
            address="Kyiv",
            paid=True,
        )
        Order.objects.create(
            first_name="Other",
            last_name="User",
            email=self.other_user.email,
            address="Lviv",
            paid=False,
        )

        self.client.login(username="testuser", password="pass12345")
        response = self.client.get(reverse("accounts:profile"))
        orders = list(response.context["user_orders"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, own_order.id)
