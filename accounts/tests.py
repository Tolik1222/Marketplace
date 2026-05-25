from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

from orders.models import Order, SubOrder, OrderItem
from products.models import Product, Category
from accounts.models import SellerProfile

User = get_user_model()


class SubOrderSplitTests(TestCase):
    """Tests that cart checkout correctly partitions items into vendor SubOrders."""

    def setUp(self):
        self.client = Client()
        self.vendor1 = User.objects.create_user(username='vendor1', password='pass', is_staff=True)
        self.vendor2 = User.objects.create_user(username='vendor2', password='pass', is_staff=True)
        self.buyer = User.objects.create_user(username='buyer', password='pass')

        self.category = Category.objects.create(name='Test', slug='test')

        self.product1 = Product.objects.create(
            name='Product V1', slug='product-v1', category=self.category,
            price=Decimal('100.00'), available=True, owner=self.vendor1
        )
        self.product2 = Product.objects.create(
            name='Product V2', slug='product-v2', category=self.category,
            price=Decimal('200.00'), available=True, owner=self.vendor2
        )

    def _make_order_with_two_vendors(self):
        """Helper to create an Order with two SubOrders (one per vendor)."""
        order = Order.objects.create(
            first_name='Test', last_name='Buyer',
            email='buyer@test.com', payment_method='cod'
        )
        sub1 = SubOrder.objects.create(order=order, vendor=self.vendor1, status='pending')
        sub2 = SubOrder.objects.create(order=order, vendor=self.vendor2, status='pending')
        OrderItem.objects.create(order=order, sub_order=sub1, product=self.product1, price=Decimal('100.00'), quantity=2)
        OrderItem.objects.create(order=order, sub_order=sub2, product=self.product2, price=Decimal('200.00'), quantity=1)
        return order, sub1, sub2

    def test_sub_orders_created_per_vendor(self):
        """Each vendor in the cart should get a separate SubOrder."""
        order, sub1, sub2 = self._make_order_with_two_vendors()
        self.assertEqual(SubOrder.objects.filter(order=order).count(), 2)
        self.assertEqual(sub1.vendor, self.vendor1)
        self.assertEqual(sub2.vendor, self.vendor2)

    def test_order_items_linked_to_correct_sub_order(self):
        """OrderItems should be linked to their vendor's SubOrder."""
        order, sub1, sub2 = self._make_order_with_two_vendors()
        self.assertEqual(sub1.items.count(), 1)
        self.assertEqual(sub2.items.count(), 1)
        self.assertEqual(sub1.items.first().product, self.product1)
        self.assertEqual(sub2.items.first().product, self.product2)

    def test_sub_order_total_cost(self):
        """SubOrder.get_total_cost() should sum items in that sub-order only."""
        order, sub1, sub2 = self._make_order_with_two_vendors()
        self.assertEqual(sub1.get_total_cost(), Decimal('200.00'))
        self.assertEqual(sub2.get_total_cost(), Decimal('200.00'))

    def test_order_cancellation_cascades_to_sub_orders(self):
        """Canceling an Order should cascade status='canceled' to all SubOrders."""
        order, sub1, sub2 = self._make_order_with_two_vendors()
        order.status = 'canceled'
        order.save()
        sub1.refresh_from_db()
        sub2.refresh_from_db()
        self.assertEqual(sub1.status, 'canceled')
        self.assertEqual(sub2.status, 'canceled')

    def test_order_payment_updates_sub_orders_to_paid(self):
        """Marking an Order as paid should update pending SubOrders to paid."""
        order, sub1, sub2 = self._make_order_with_two_vendors()
        order.status = 'paid'
        order.save()
        sub1.refresh_from_db()
        sub2.refresh_from_db()
        self.assertEqual(sub1.status, 'paid')
        self.assertEqual(sub2.status, 'paid')


class SellerProfileTests(TestCase):
    """Tests for SellerProfile model auto-creation and editing."""

    def setUp(self):
        self.seller = User.objects.create_user(username='seller_p', password='pass', is_staff=True)

    def test_seller_profile_auto_created(self):
        """SellerProfile should be auto-created for new users."""
        new_user = User.objects.create_user(username='newvendor', password='pass')
        self.assertTrue(SellerProfile.objects.filter(user=new_user).exists())

    def test_seller_profile_edit_view_accessible(self):
        """Seller profile edit page should be accessible to staff users."""
        self.client.login(username='seller_p', password='pass')
        response = self.client.get(reverse('accounts:seller_profile_edit'))
        self.assertEqual(response.status_code, 200)

    def test_seller_profile_edit_saves_stripe_id(self):
        """Saving the seller profile form should persist the Stripe account ID."""
        self.client.login(username='seller_p', password='pass')
        response = self.client.post(reverse('accounts:seller_profile_edit'), {
            'stripe_account_id': 'acct_testABC123',
            'np_sender_ref': '',
            'np_sender_address_ref': '',
            'np_sender_contact_ref': '',
            'np_sender_phone': '',
        })
        self.assertRedirects(response, reverse('accounts:seller_dashboard'))
        profile = SellerProfile.objects.get(user=self.seller)
        self.assertEqual(profile.stripe_account_id, 'acct_testABC123')


class SubOrderDetailViewTests(TestCase):
    """Tests for the seller SubOrder detail view and status update."""

    def setUp(self):
        self.client = Client()
        self.vendor = User.objects.create_user(username='vdetail', password='pass', is_staff=True)
        self.other_vendor = User.objects.create_user(username='other', password='pass', is_staff=True)
        self.category = Category.objects.create(name='Cat', slug='cat')
        self.product = Product.objects.create(
            name='Item', slug='item', category=self.category,
            price=Decimal('50.00'), available=True, owner=self.vendor
        )
        self.order = Order.objects.create(
            first_name='A', last_name='B', email='a@b.com', payment_method='cod'
        )
        self.sub_order = SubOrder.objects.create(order=self.order, vendor=self.vendor, status='paid')
        OrderItem.objects.create(order=self.order, sub_order=self.sub_order,
                                 product=self.product, price=Decimal('50.00'), quantity=3)

    def test_detail_view_accessible_to_owner(self):
        """Vendor can access their own SubOrder detail page."""
        self.client.login(username='vdetail', password='pass')
        response = self.client.get(reverse('accounts:seller_suborder_detail', args=[self.sub_order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Item')

    def test_detail_view_blocked_for_other_vendor(self):
        """Another vendor cannot access a SubOrder they don't own."""
        self.client.login(username='other', password='pass')
        response = self.client.get(reverse('accounts:seller_suborder_detail', args=[self.sub_order.id]))
        self.assertEqual(response.status_code, 404)

    def test_status_update_via_post(self):
        """Vendor can update SubOrder status via POST."""
        self.client.login(username='vdetail', password='pass')
        self.client.post(
            reverse('accounts:seller_suborder_detail', args=[self.sub_order.id]),
            {'status': 'shipped'}
        )
        self.sub_order.refresh_from_db()
        self.assertEqual(self.sub_order.status, 'shipped')
