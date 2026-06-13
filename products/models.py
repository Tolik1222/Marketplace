from decimal import Decimal

from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="user_products",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(90)],
    )
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        cache.clear()
        super().save(*args, **kwargs)
        try:
            from .search import index_product
            index_product(self)
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        product_id = self.id
        from django.core.cache import cache
        cache.clear()
        super().delete(*args, **kwargs)
        try:
            from .search import remove_product
            remove_product(product_id)
        except Exception:
            pass

    @property
    def has_discount(self):
        return self.discount_percent > 0

    def get_discounted_price(self):
        if not self.has_discount:
            return self.price
        multiplier = Decimal("1") - (Decimal(self.discount_percent) / Decimal("100"))
        return (self.price * multiplier).quantize(Decimal("0.01"))

    @property
    def get_average_rating(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0.0
        return sum(r.rating for r in reviews) / len(reviews)


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.product}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product} ({self.rating})"


class PromoBanner(models.Model):
    badge_text = models.CharField("Текст бейджа", max_length=50, default="АКЦІЯ", help_text="Наприклад: 'АКЦІЯ' або 'NEW ARRIVAL'")
    badge_class = models.CharField(
        "Стиль бейджа (Bootstrap)", 
        max_length=50, 
        default="bg-primary", 
        choices=[
            ('bg-primary', 'Primary (Синій)'),
            ('bg-info text-dark', 'Info (Блакитний)'),
            ('bg-danger', 'Danger (Червоний)'),
            ('bg-warning text-dark', 'Warning (Жовтий)'),
            ('bg-success', 'Success (Зелений)'),
        ]
    )
    
    title = models.CharField("Головний заголовок", max_length=250, help_text="Наприклад: 'Нова ера геймінгу:' або 'Легендарний дизайн'")
    title_highlight = models.CharField(
        "Виділена частина заголовка (сяйво)", 
        max_length=200, 
        blank=True, 
        help_text="Частина заголовка, що буде світитися синім кольором. Наприклад: 'HP Victus серія' або 'iPhone 12'"
    )
    
    description = models.TextField("Опис", blank=True, help_text="Короткий опис пропозиції.")
    image = models.ImageField("Зображення товару", upload_to='promo_banners/', help_text="Зображення прозорого ноутбука, телефону тощо.")
    
    button_text = models.CharField("Текст кнопки", max_length=100, default="КУПИТИ ЗАРАЗ")
    button_class = models.CharField(
        "Стиль кнопки (Bootstrap)", 
        max_length=50, 
        default="btn-primary",
        choices=[
            ('btn-primary', 'Primary (Синій)'),
            ('btn-info', 'Info (Блакитний)'),
            ('btn-danger', 'Danger (Червоний)'),
            ('btn-success', 'Success (Зелений)'),
        ]
    )
    link_url = models.CharField("Посилання для кнопки", max_length=255, default="?q=HP+Victus", help_text="URL або пошуковий запит куди веде кнопка.")
    
    background_style = models.CharField(
        "Стиль фону (CSS Gradient)", 
        max_length=300, 
        default="linear-gradient(135deg, #070c1e 0%, #0d1a3a 100%)",
        help_text="CSS градієнт для фону картки. Наприклад: 'linear-gradient(135deg, #091a3c 0%, #1e3a8a 100%)'"
    )
    
    is_active = models.BooleanField("Активний", default=True, help_text="Якщо вимкнено, банер не відображатиметься.")
    order = models.PositiveIntegerField("Порядок відображення", default=0, help_text="Сортування від меншого до більшого.")

    class Meta:
        ordering = ['order', '-id']
        verbose_name = "Промо банер"
        verbose_name_plural = "Промо банери"

    def __str__(self):
        return f"{self.badge_text}: {self.title} {self.title_highlight}"

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        cache.clear()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.cache import cache
        cache.clear()
        super().delete(*args, **kwargs)


class TrendingCategory(models.Model):
    """Картки «Актуальні категорії» на головній сторінці."""

    ICON_CHOICES = [
        ('bi-laptop', 'Ноутбук (bi-laptop)'),
        ('bi-laptop-fill', 'Ноутбук заповнений (bi-laptop-fill)'),
        ('bi-pc-display', 'Монітор (bi-pc-display)'),
        ('bi-mouse', 'Миша (bi-mouse)'),
        ('bi-phone', 'Телефон (bi-phone)'),
        ('bi-headphones', 'Навушники (bi-headphones)'),
        ('bi-keyboard', 'Клавіатура (bi-keyboard)'),
        ('bi-cpu', 'Процесор (bi-cpu)'),
        ('bi-hdd', 'Диск (bi-hdd)'),
        ('bi-printer', 'Принтер (bi-printer)'),
        ('bi-camera', 'Камера (bi-camera)'),
        ('bi-controller', 'Геймпад (bi-controller)'),
        ('bi-smartwatch', 'Розумний годинник (bi-smartwatch)'),
        ('bi-tablet', 'Планшет (bi-tablet)'),
    ]

    GRADIENT_CHOICES = [
        ('linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', 'Темно-синій'),
        ('linear-gradient(135deg, #4c1d95 0%, #1e1b4b 100%)', 'Фіолетовий'),
        ('linear-gradient(135deg, #0369a1 0%, #0c4a6e 100%)', 'Блакитний'),
        ('linear-gradient(135deg, #4b5563 0%, #1f2937 100%)', 'Сірий'),
        ('linear-gradient(135deg, #065f46 0%, #022c22 100%)', 'Зелений'),
        ('linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)', 'Червоний'),
    ]

    BORDER_COLOR_CHOICES = [
        ('rgba(59, 130, 246, 0.15)', 'Синій'),
        ('rgba(139, 92, 246, 0.15)', 'Фіолетовий'),
        ('rgba(14, 165, 233, 0.15)', 'Блакитний'),
        ('rgba(156, 163, 175, 0.15)', 'Сірий'),
        ('rgba(52, 211, 153, 0.15)', 'Зелений'),
        ('rgba(248, 113, 113, 0.15)', 'Червоний'),
    ]

    name_uk = models.CharField('Назва (UA)', max_length=100, help_text='Назва картки українською, наприклад: Геймерські ноутбуки')
    name_en = models.CharField('Назва (EN)', max_length=100, help_text='Назва картки англійською, наприклад: Gaming Laptops')
    icon = models.CharField('Bootstrap іконка', max_length=50, choices=ICON_CHOICES, default='bi-laptop')
    gradient = models.CharField(
        'CSS градієнт фону', max_length=200,
        choices=GRADIENT_CHOICES,
        default='linear-gradient(135deg, #1e293b 0%, #0f172a 100%)'
    )
    border_color = models.CharField(
        'Колір рамки', max_length=60,
        choices=BORDER_COLOR_CHOICES,
        default='rgba(59, 130, 246, 0.15)'
    )
    hover_shadow = models.CharField(
        'Тінь при hover', max_length=80,
        default='rgba(59, 130, 246, 0.2)',
        help_text='Колір тіні картки при наведенні, наприклад: rgba(59, 130, 246, 0.2)'
    )
    search_query = models.CharField(
        'Пошуковий запит', max_length=200,
        help_text='Запит для кнопки, наприклад: геймер або ultrabook. Формується як ?q=...'
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='trending_cards',
        verbose_name='Прив\'язані категорії',
        help_text='Товари з цих категорій потраплять до цього блоку при перегляді'
    )
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Актуальна категорія'
        verbose_name_plural = 'Актуальні категорії'

    def __str__(self):
        return self.name_uk

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        cache.clear()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.cache import cache
        cache.clear()
        super().delete(*args, **kwargs)
