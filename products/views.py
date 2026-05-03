from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify # автоматичне створення slug
from .models import Category, Product, Review, WishlistItem
from .forms import ProductForm, ReviewForm

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

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(
            WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, 'products/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'wishlist_ids': wishlist_ids,
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
    reviews = product.reviews.select_related("user")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]

    bought_together = Product.objects.filter(
        order_items__order__items__product=product
    ).exclude(id=product.id).distinct()[:4]
    similar_products = Product.objects.filter(category=product.category, available=True).exclude(id=product.id)[:4]
    recommendations = list(bought_together)
    for candidate in similar_products:
        if len(recommendations) >= 4:
            break
        if candidate not in recommendations:
            recommendations.append(candidate)

    can_review = False
    existing_review = None
    if request.user.is_authenticated:
        can_review = product.order_items.filter(order__email=request.user.email).exists()
        existing_review = Review.objects.filter(product=product, user=request.user).first()

    return render(
        request,
        'products/product/detail.html',
        {
            'product': product,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'recommendations': recommendations,
            'can_review': can_review,
            'existing_review': existing_review,
            'review_form': ReviewForm(instance=existing_review),
        },
    )


def shipping_payment(request):
    return render(request, 'products/pages/shipping_payment.html')


@login_required
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    item = WishlistItem.objects.filter(user=request.user, product=product).first()
    if item:
        item.delete()
        messages.info(request, "Товар прибрано зі списку бажань.")
    else:
        WishlistItem.objects.create(user=request.user, product=product)
        messages.success(request, "Товар додано до списку бажань.")
    return redirect(request.META.get("HTTP_REFERER", "products:product_list"))


@login_required
def wishlist_list(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("product")
    return render(request, "products/product/wishlist.html", {"items": items})


@login_required
def review_create(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    if not product.order_items.filter(order__email=request.user.email).exists():
        messages.error(request, "Відгук можна залишити тільки після покупки товару.")
        return redirect("products:product_detail", id=product.id, slug=product.slug)

    review = Review.objects.filter(product=product, user=request.user).first()
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == "POST" and form.is_valid():
        new_review = form.save(commit=False)
        new_review.product = product
        new_review.user = request.user
        new_review.save()
        messages.success(request, "Дякуємо за ваш відгук!")
    return redirect("products:product_detail", id=product.id, slug=product.slug)