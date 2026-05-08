from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order


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
