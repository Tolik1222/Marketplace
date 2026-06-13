from django.contrib import admin
from .models import Category, Product, Review, WishlistItem, PromoBanner, TrendingCategory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'discount_percent', 'available', 'created']
    list_filter = ['available', 'discount_percent', 'created']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "product__name"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["product__name", "user__username", "comment"]


@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'badge_text', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'badge_text']
    search_fields = ['title', 'title_highlight', 'description']


@admin.register(TrendingCategory)
class TrendingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name_uk', 'name_en', 'icon', 'search_query', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name_uk', 'name_en', 'search_query']
    filter_horizontal = ['categories']
    fieldsets = [
        ('Назва', {'fields': ['name_uk', 'name_en']}),
        ('Вигляд', {'fields': ['icon', 'gradient', 'border_color', 'hover_shadow']}),
        ('Поведінка', {'fields': ['search_query', 'categories']}),
        ('Налаштування', {'fields': ['is_active', 'order']}),
    ]