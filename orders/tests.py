from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from products.models import Product, Category
from orders.models import Order, Coupon, OrderItem

User = get_user_model()

class OrdersAndCouponsTests(TestCase):
    def setUp(self):
        # створюємо тестову категорію та товар
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('500.00'),
            category=self.category,
            available=True
        )
        
    def test_percentage_coupon_discount(self):
        # створюємо відсотковий купон (10% знижки)
        coupon = Coupon.objects.create(
            code='PERCENT10',
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            discount=10,
            discount_type='percentage',
            active=True
        )
        order = Order.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            coupon=coupon,
            discount=10
        )
        OrderItem.objects.create(order=order, product=self.product, price=Decimal('500.00'), quantity=2)
        
        # сума без знижки: 500 * 2 = 1000. Знижка 10% - це 100.
        self.assertEqual(order.get_total_cost(), Decimal('1000.00'))
        self.assertEqual(order.get_discount_amount(), Decimal('100.00'))
        self.assertEqual(order.get_total_after_discount(), Decimal('900.00'))

    def test_fixed_coupon_discount(self):
        # фіксований купон (мінус 150 грн)
        coupon = Coupon.objects.create(
            code='FIXED150',
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            discount_type='fixed',
            discount_value=Decimal('150.00'),
            active=True
        )
        order = Order.objects.create(
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            coupon=coupon
        )
        OrderItem.objects.create(order=order, product=self.product, price=Decimal('500.00'), quantity=2)
        
        # сума без знижки: 1000, знижка: 150, разом: 850.
        self.assertEqual(order.get_total_cost(), Decimal('1000.00'))
        self.assertEqual(order.get_discount_amount(), Decimal('150.00'))
        self.assertEqual(order.get_total_after_discount(), Decimal('850.00'))

    def test_fixed_coupon_exceeds_total(self):
        # фіксований купон на 150 грн
        coupon = Coupon.objects.create(
            code='FIXED150',
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            discount_type='fixed',
            discount_value=Decimal('150.00'),
            active=True
        )
        order = Order.objects.create(
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            coupon=coupon
        )
        # товар коштує лише 100 грн
        OrderItem.objects.create(order=order, product=self.product, price=Decimal('100.00'), quantity=1)
        
        # знижка не може бути більшою за суму замовлення
        self.assertEqual(order.get_total_cost(), Decimal('100.00'))
        self.assertEqual(order.get_discount_amount(), Decimal('100.00'))
        self.assertEqual(order.get_total_after_discount(), Decimal('0.00'))


class SellerDashboardAndPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        
        # створюємо продавця
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='password123',
            is_staff=True
        )
        
        # створюємо звичайного покупця
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='password123',
            is_staff=False
        )

        # створюємо 8 товарів для перевірки пагінації
        self.products = []
        for i in range(8):
            p = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                price=Decimal('100.00') + i,
                category=self.category,
                available=True,
                owner=self.seller
            )
            self.products.append(p)

    def test_seller_dashboard_permission_denied_for_buyers(self):
        # логінимось як покупець
        self.client.login(username='buyer', password='password123')
        response = self.client.get(reverse('accounts:seller_dashboard'))
        self.assertEqual(response.status_code, 403) # перевіряємо, що покупцю вхід закритий (повертає 403)

    def test_seller_dashboard_allowed_for_sellers(self):
        # логінимось як продавець
        self.client.login(username='seller', password='password123')
        response = self.client.get(reverse('accounts:seller_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/seller_dashboard.html')

    def test_catalog_pagination_per_6_items(self):
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # перевіряємо товари в контексті
        products_on_page = response.context['products']
        # пагінатор має розділити 8 товарів: 6 на першій сторінці, 2 на другій
        self.assertEqual(len(products_on_page), 6)
        
        # переходимо на другу сторінку
        response_page_2 = self.client.get(reverse('products:product_list') + '?page=2')
        self.assertEqual(response_page_2.status_code, 200)
        products_on_page_2 = response_page_2.context['products']
        self.assertEqual(len(products_on_page_2), 2)


from django.core.cache import cache

class Phase2FeaturesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        
        # створюємо покупця та продавця
        self.seller = User.objects.create_user(
            username='seller2',
            email='seller2@example.com',
            password='password123',
            is_staff=True
        )
        self.buyer = User.objects.create_user(
            username='buyer2',
            email='buyer2@example.com',
            password='password123',
            is_staff=False
        )
        
        # створюємо товар продавця
        self.product = Product.objects.create(
            name='Fancy Chair',
            slug='fancy-chair',
            price=Decimal('250.00'),
            category=self.category,
            available=True,
            owner=self.seller
        )
        
        cache.clear()

    def test_novaposhta_cities_ajax(self):
        # автокомпліт міст має повертати список JSON
        response = self.client.get(reverse('orders:novaposhta_cities') + '?q=Киї')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('name', data[0])
            self.assertIn('ref', data[0])

    def test_novaposhta_branches_ajax(self):
        response = self.client.get(reverse('orders:novaposhta_branches') + '?city_ref=db5c88f5-391c-11dd-90d9-001a4d12cfd8')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('name', data[0])
            self.assertIn('ref', data[0])

    def test_seller_export_excel_permissions_and_download(self):
        # 1. анонімного користувача редиректить на логін
        response = self.client.get(reverse('accounts:seller_export_excel'))
        self.assertEqual(response.status_code, 302)
        
        # 2. покупець отримує 403
        self.client.login(username='buyer2', password='password123')
        response = self.client.get(reverse('accounts:seller_export_excel'))
        self.assertEqual(response.status_code, 403)
        
        # 3. продавець отримує excel файл
        self.client.login(username='seller2', password='password123')
        response = self.client.get(reverse('accounts:seller_export_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_caching_and_cache_invalidation(self):
        # очищуємо кеш перед тестом
        cache.clear()
        
        # кешування каталогу товарів
        cache_key = "products_query_all___all_newest_"
        self.assertIsNone(cache.get(cache_key))
        
        # робимо запит до сторінки каталогу
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # тепер дані мають бути в кеші
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 1)
        self.assertEqual(cached_data[0].id, self.product.id)
        
        # змінюємо товар — кеш має скинутись
        self.product.price = Decimal('300.00')
        self.product.save()
        
        # перевіряємо, що кеш очистився
        self.assertIsNone(cache.get(cache_key))

    def test_ukrposhta_and_meest_ajax(self):
        # 1. автокомпліт міст Укрпошти
        response = self.client.get(reverse('orders:ukrposhta_cities') + '?q=Киї')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

        # 2. автокомпліт відділень Укрпошти
        response = self.client.get(reverse('orders:ukrposhta_branches') + '?city_ref=ukr-ref')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json()[0]['name'], 'Головне відділення Укрпошти №1 (вул. Хрещатик, 22)')

        # 3. автокомпліт міст Meest
        response = self.client.get(reverse('orders:meest_cities') + '?q=Хар')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

        # 4. автокомпліт відділень Meest
        response = self.client.get(reverse('orders:meest_branches') + '?city_ref=meest-ref')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json()[0]['name'], 'Міні-відділення Meest №125 (супермаркет "Сільпо", вул. Басейна, 12)')

    def test_product_comparison_ajax_and_view(self):
        # 1. додаємо товар у порівняння
        response = self.client.get(reverse('products:compare_toggle', args=[self.product.id]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['added'])
        self.assertEqual(data['count'], 1)

        # 2. видаляємо товар з порівняння
        response = self.client.get(reverse('products:compare_toggle', args=[self.product.id]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['added'])
        self.assertEqual(data['count'], 0)

        # 3. додаємо знову і перевіряємо сторінку порівняння
        self.client.get(reverse('products:compare_toggle', args=[self.product.id]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.get(reverse('products:compare_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fancy Chair')

    def test_multilingual_setlang(self):
        # змінюємо мову на англійську
        response = self.client.post(reverse('set_language'), data={'language': 'en', 'next': '/'})
        self.assertEqual(response.status_code, 302)
        
        # кука мови має змінитись на 'en'
        self.assertEqual(self.client.cookies['django_language'].value, 'en')

    def test_payment_method_selection(self):
        from orders.forms import OrderCreateForm
        from orders.models import Order
        
        # 1. вибір методів оплати для звичайних товарів
        form_no_expensive = OrderCreateForm(has_expensive_item=False)
        choices_no_expensive = dict(form_no_expensive.fields['payment_method'].choices)
        self.assertIn('card', choices_no_expensive)
        self.assertIn('cod', choices_no_expensive)
        self.assertNotIn('partial', choices_no_expensive)

        # 2. вибір методів для дорогих товарів (з'являється 10% передплата)
        form_expensive = OrderCreateForm(has_expensive_item=True)
        choices_expensive = dict(form_expensive.fields['payment_method'].choices)
        self.assertIn('card', choices_expensive)
        self.assertIn('cod', choices_expensive)
        self.assertIn('partial', choices_expensive)

        # 3. при накладеному платежі редиректить одразу на успішну сторінку
        # додаємо товар у кошик сесії
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'quantity': 1,
                'price': str(self.product.price)
            }
        }
        session.save()

        form_data = {
            'first_name': 'Ivan',
            'last_name': 'Petrov',
            'email': 'ivan@example.com',
            'delivery_service': 'nova_poshta',
            'city': 'Київ',
            'branch': 'Відділення №1',
            'address': '',
            'payment_method': 'cod',
        }
        response = self.client.post(reverse('orders:order_create'), data=form_data)
        self.assertRedirects(response, reverse('payment:completed'))

        # перевіряємо збережений метод оплати
        order = Order.objects.latest('id')
        self.assertEqual(order.payment_method, 'cod')
