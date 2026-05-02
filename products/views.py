from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify # автоматичне створення slug
from .models import Category, Product
from .forms import ProductForm

# функція списку
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'products/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query
    })

# для додавання товару
def product_add(request):
    # щоб тільки адмін міг додавати:
    # if not request.user.is_staff:
    #     return redirect('products:product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.slug = slugify(product.name)
            product.save()
            return redirect('products:product_list')
    else:
        form = ProductForm()
    
    return render(request, 'products/product/add.html', {'form': form})

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    return render(request, 'products/product/detail.html', {'product': product})