from django.db import models
from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'delivery_service', 'city', 'branch', 'address', 'payment_method']
        labels = {
            "first_name": "Ім'я",
            "last_name": "Прізвище",
            "email": "Email",
            "delivery_service": "Служба доставки",
            "city": "Місто",
            "branch": "Відділення пошти",
            "address": "Додаткова адреса (за потреби)",
            "payment_method": "Спосіб оплати",
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
            "delivery_service": forms.Select(
                attrs={
                    "class": "form-select form-select-lg",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Оберіть або введіть місто",
                }
            ),
            "branch": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Оберіть або введіть відділення пошти",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Вулиця, будинок, квартира (опціонально)",
                    "rows": 2,
                    "autocomplete": "street-address",
                }
            ),
            "payment_method": forms.Select(
                attrs={
                    "class": "form-select form-select-lg",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        has_expensive_item = kwargs.pop('has_expensive_item', False)
        from django.utils.translation import get_language
        lang = get_language()
        super().__init__(*args, **kwargs)
        
        if lang == 'en':
            self.fields['first_name'].label = "First Name"
            self.fields['last_name'].label = "Last Name"
            self.fields['email'].label = "Email"
            self.fields['delivery_service'].label = "Delivery Service"
            self.fields['city'].label = "City"
            self.fields['branch'].label = "Branch"
            self.fields['address'].label = "Additional Address (optional)"
            self.fields['payment_method'].label = "Payment Method"
            
            self.fields['first_name'].widget.attrs['placeholder'] = "Enter your first name"
            self.fields['last_name'].widget.attrs['placeholder'] = "Enter your last name"
            self.fields['address'].widget.attrs['placeholder'] = "Street, building, apartment (optional)"
            
            self.fields['delivery_service'].choices = [
                ('nova_poshta', 'Nova Poshta'),
                ('ukr_poshta', 'Ukrposhta'),
                ('meest', 'Meest')
            ]
            
            if not has_expensive_item:
                self.fields['payment_method'].choices = [
                    ('card', 'Card Payment'),
                    ('cod', 'Cash on Delivery'),
                ]
            else:
                self.fields['payment_method'].choices = [
                    ('card', 'Card Payment'),
                    ('cod', 'Cash on Delivery'),
                    ('partial', '10% Deposit (for orders > 10,000 UAH)'),
                ]
        else:
            if not has_expensive_item:
                self.fields['payment_method'].choices = [
                    ('card', 'Оплата карткою'),
                    ('cod', 'Накладений платіж'),
                ]
            else:
                self.fields['payment_method'].choices = [
                    ('card', 'Оплата карткою'),
                    ('cod', 'Накладений платіж'),
                    ('partial', 'Внесок 10% від вартості замовлення (для товарів > 10 000 грн)'),
                ]