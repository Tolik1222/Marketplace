from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order
from products.models import Product, Category


@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
class StripeWebhookTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            address="Kyiv",
        )
        self.url = reverse("payment:stripe_webhook")

    @patch("payment.views.stripe.Webhook.construct_event")
    def test_webhook_marks_order_paid(self, mock_construct_event):
        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": SimpleNamespace(
                    mode="payment",
                    payment_status="paid",
                    client_reference_id=str(self.order.id),
                )
            },
        }

        response = self.client.post(
            self.url,
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signature",
        )

        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.order.paid)

    @patch("payment.views.stripe.Webhook.construct_event")
    def test_webhook_is_idempotent_for_paid_order(self, mock_construct_event):
        self.order.paid = True
        self.order.save(update_fields=["paid"])
        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "mode": "payment",
                    "payment_status": "paid",
                    "client_reference_id": str(self.order.id),
                }
            },
        }

        response = self.client.post(
            self.url,
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signature",
        )

        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.order.paid)


class StripePaymentProcessTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            address="Kyiv",
            discount=10,  # 10% discount
        )
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            price=100.00,
            slug="test-product",
            available=True,
        )
        from orders.models import OrderItem
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=100.00,
            quantity=1,
        )
        self.url = reverse("payment:process")

    @patch("payment.views.stripe.checkout.Session.create")
    def test_payment_process_applies_discount(self, mock_session_create):
        session = self.client.session
        session["order_id"] = self.order.id
        session.save()

        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_session_create.return_value = mock_session

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("https://checkout.stripe.com"))

        mock_session_create.assert_called_once()
        called_kwargs = mock_session_create.call_args[1]
        line_items = called_kwargs["line_items"]

        # Expected price: 100 * (100 - 10) / 100 = 90.00 -> 9000 cents
        self.assertEqual(len(line_items), 1)
        self.assertEqual(line_items[0]["price_data"]["unit_amount"], 9000)
        self.assertEqual(line_items[0]["price_data"]["currency"], "uah")
        self.assertEqual(line_items[0]["price_data"]["product_data"]["name"], "Test Product")

