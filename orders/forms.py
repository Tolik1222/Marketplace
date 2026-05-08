from django.db import models
from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address']
        labels = {
            "first_name": "Ім'я",
            "last_name": "Прізвище",
            "email": "Email",
            "address": "Адреса доставки",
        }
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Введіть ваше ім'я",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Введіть ваше прізвище",
                    "autocomplete": "family-name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "example@email.com",
                    "autocomplete": "email",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Місто, вулиця, будинок, квартира",
                    "rows": 3,
                    "autocomplete": "street-address",
                }
            ),
        }