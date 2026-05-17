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

    def __init__(self, *args, **kwargs):
        from django.utils.translation import get_language
        lang = get_language()
        super().__init__(*args, **kwargs)
        if lang == 'en':
            self.fields['subject'].label = "Subject"
            self.fields['subject'].widget.attrs['placeholder'] = "e.g. Issue with order payment"
            self.fields['message'].label = "Message"
            self.fields['message'].widget.attrs['placeholder'] = "Describe your issue or request..."


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

    def __init__(self, *args, **kwargs):
        from django.utils.translation import get_language
        lang = get_language()
        super().__init__(*args, **kwargs)
        if lang == 'en':
            self.fields['message'].widget.attrs['placeholder'] = "Write a reply..."
