from django.contrib import admin
from .models import Coupon, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'address', 'paid', 'created']
    list_filter = ['paid', 'created']
    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount", "valid_from", "valid_to", "active"]
    list_filter = ["active", "valid_from", "valid_to"]
    search_fields = ["code"]