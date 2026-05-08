# Marketplace (Django)

Повноцінний навчально-практичний маркетплейс на Django з каталогом товарів, кошиком, купонами, замовленнями, оплатою через Stripe та системою підтримки.

## Що реалізовано

- Реєстрація, логін, профіль користувача (`accounts`)
- Каталог товарів з категоріями, пошуком, wishlist і відгуками (`products`)
- Фільтри та сортування каталогу (ціна, наявність, тип сортування)
- Система знижок на товари + акційний блок у каталозі
- Кошик на сесіях + промокоди (`cart`)
- Оформлення замовлень (`orders`)
- Онлайн-оплата через Stripe Checkout + webhook (`payment`)
- Тікети підтримки (`support`)
- Історія замовлень у профілі користувача (`accounts`)
- Адмін-панель Django для керування даними

## Технологічний стек

- Python 3.11+
- Django 4.2.x
- Stripe API
- Cloudinary (медіа/статика)
- PostgreSQL або SQLite (через `dj-database-url`)
- Gunicorn (для деплою)

## Структура проєкту

- `config/` - налаштування Django і головні URL.
- `products/` - товари, категорії, відгуки, wishlist.
- `cart/` - логіка кошика і застосування купонів.
- `orders/` - створення замовлень і позицій.
- `payment/` - Stripe checkout та webhook.
- `accounts/` - автентифікація і профіль.
- `support/` - тікети та повідомлення підтримки.
- `templates/` - HTML-шаблони.

## Швидкий старт (локально)

1. Встановіть залежності:
   - `pip install -r requirements.txt`
2. Створіть `.env` у корені проєкту.
3. Виконайте міграції:
   - `python manage.py migrate`
4. Запустіть сервер:
   - `python manage.py runserver`

## Змінні оточення

Мінімально рекомендовані:

- `DJANGO_SECRET_KEY` - секретний ключ Django.
- `DJANGO_DEBUG` - `true/false`.
- `DJANGO_ALLOWED_HOSTS` - список хостів через кому.
- `DATABASE_URL` - рядок підключення до БД.

Для платежів:

- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_API_VERSION`
- `STRIPE_WEBHOOK_SECRET`

Для нотифікацій:

- `DEFAULT_FROM_EMAIL`
- `EMAIL_BACKEND`
- `ORDER_ADMIN_EMAIL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Додатково (безпека):

- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`
- `DJANGO_LOG_LEVEL`


## Запуск тестів

- Усі тести:
  - `python manage.py test`
- Точково:
  - `python manage.py test products.tests payment.tests`


### Бізнес-логіка

- Ролі `buyer/seller/admin` з чіткими правами.
- Кабінет продавця (CRUD товарів, статистика продажів).
- Підтримка повернень/скасувань замовлень.
- Гнучкі типи промокодів (фіксована сума, free shipping).

## Деплой (базовий чеклист)

- Налаштовані змінні середовища.
- Вимкнений `DEBUG`.
- Заповнений `DJANGO_ALLOWED_HOSTS`.
- Працюють міграції та `collectstatic`.
- Stripe webhook направлений на `/payment/webhook/`.
- Перевірено email/нотифікації.
- Увімкнено логування і збір помилок.

## Сервер

Проект був задеплоєний на безкошновному сервері Render, тому лінк:
https://marketplace-9ij0.onrender.com
Але немає 100% впевненості що він буде працювати довго :)
