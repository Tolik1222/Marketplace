from django.shortcuts import render, get_object_or_404
from .models import Category, Product

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    # Фільтрація за категорією
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # За назвою пошук
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'products/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query
    })