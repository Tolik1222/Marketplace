from django import forms
from .models import Product, Review

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'image', 'description', 'price', 'discount_percent', 'available']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 90}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'en':
            self.fields['category'].label = 'Category'
            self.fields['name'].label = 'Product Name'
            self.fields['name'].widget.attrs['placeholder'] = 'Product name'
            self.fields['image'].label = 'Image'
            self.fields['description'].label = 'Description'
            self.fields['description'].widget.attrs['placeholder'] = 'Product description...'
            self.fields['price'].label = 'Price (UAH)'
            self.fields['discount_percent'].label = 'Discount (%)'
            self.fields['available'].label = 'Available'
        else:
            self.fields['category'].label = 'Категорія'
            self.fields['name'].label = 'Назва товару'
            self.fields['name'].widget.attrs['placeholder'] = 'Назва продукту'
            self.fields['image'].label = 'Зображення'
            self.fields['description'].label = 'Опис'
            self.fields['description'].widget.attrs['placeholder'] = 'Опис продукту...'
            self.fields['price'].label = 'Ціна (грн)'
            self.fields['discount_percent'].label = 'Відсоток знижки'
            self.fields['available'].label = 'Доступний для продажу'


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, f"{i} ★") for i in range(5, 0, -1)],
                attrs={"class": "form-select"},
            ),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'en':
            self.fields['rating'].label = 'Rating'
            self.fields['comment'].label = 'Comment'
            self.fields['comment'].widget.attrs['placeholder'] = 'Your review...'
        else:
            self.fields['rating'].label = 'Рейтинг'
            self.fields['comment'].label = 'Коментар'
            self.fields['comment'].widget.attrs['placeholder'] = 'Ваш відгук...'