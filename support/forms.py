from django import forms

from .models import SupportMessage, SupportTicket


class SupportTicketCreateForm(forms.ModelForm):
    message = forms.CharField(
        label="Повідомлення",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Опишіть вашу проблему або запит...",
            }
        ),
    )

    class Meta:
        model = SupportTicket
        fields = ["subject"]
        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Наприклад: Проблема з оплатою замовлення",
                }
            )
        }


class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Напишіть відповідь...",
                }
            )
        }
