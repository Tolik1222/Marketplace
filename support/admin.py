from django.contrib import admin

from .models import SupportMessage, SupportTicket


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ["author", "is_staff_reply", "created_at"]


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["id", "subject", "user", "status", "updated_at"]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = ["subject", "user__username", "user__email"]
    inlines = [SupportMessageInline]


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ["ticket", "author", "is_staff_reply", "created_at"]
    list_filter = ["is_staff_reply", "created_at"]
    search_fields = ["ticket__subject", "author__username", "message"]
