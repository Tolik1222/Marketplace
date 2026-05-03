from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    STATUS_OPEN = "open"
    STATUS_ANSWERED = "answered"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Відкрито"),
        (STATUS_ANSWERED, "Є відповідь"),
        (STATUS_CLOSED, "Закрито"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    subject = models.CharField("Тема", max_length=180)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Тікет підтримки"
        verbose_name_plural = "Тікети підтримки"

    def __str__(self):
        return f"#{self.id} {self.subject}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField("Повідомлення")
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Повідомлення підтримки"
        verbose_name_plural = "Повідомлення підтримки"

    def __str__(self):
        return f"Ticket #{self.ticket_id} by {self.author}"
