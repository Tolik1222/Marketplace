from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.core.cache import cache
from .models import Category, Product, Review, WishlistItem, PromoBanner, TrendingCategory
from .forms import ProductForm, ReviewForm

# функція списку
def product_list(request, category_slug=None):
    categories = cache.get_or_set("categories_all", lambda: list(Category.objects.all()), 600)
    
    category = None
    if category_slug:
        category = cache.get_or_set(f"category_obj_{category_slug}", lambda: get_object_or_404(Category, slug=category_slug), 600)

    query = request.GET.get('q', '')
    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    availability = request.GET.get("availability", "all")
    sort = request.GET.get("sort", "newest")
    trending_id = request.GET.get("trending_id", "")

    # Resolve TrendingCategory filter
    active_trending = None
    trending_category_ids = []
    if trending_id:
        try:
            active_trending = TrendingCategory.objects.prefetch_related('categories').get(id=int(trending_id), is_active=True)
            trending_category_ids = list(active_trending.categories.values_list('id', flat=True))
        except (TrendingCategory.DoesNotExist, ValueError):
            trending_id = ""

    # Construct unique cache key for the query results before pagination
    query_cache_key = f"products_query_{category_slug or 'all'}_{price_min}_{price_max}_{availability}_{sort}_{query}_{trending_id}"
    
    products_list = cache.get(query_cache_key)
    if products_list is None:
        products_query = Product.objects.filter(available=True)
        if category:
            products_query = products_query.filter(category=category)
        elif trending_category_ids:
            products_query = products_query.filter(category_id__in=trending_category_ids)
        
        meili_used = False
        meili_ids = None
        if query:
            from .search import search_products_meili
            meili_ids = search_products_meili(query, category_id=category.id if category else None)
            if meili_ids is not None:
                meili_used = True
                if meili_ids:
                    products_query = products_query.filter(id__in=meili_ids)
                else:
                    products_query = products_query.none()
            else:
                products_query = products_query.filter(Q(name__icontains=query) | Q(description__icontains=query))

        if price_min:
            try:
                products_query = products_query.filter(price__gte=float(price_min))
            except ValueError:
                price_min = ""
        if price_max:
            try:
                products_query = products_query.filter(price__lte=float(price_max))
            except ValueError:
                price_max = ""

        if availability == "in_stock":
            products_query = products_query.filter(available=True)

        if meili_used and sort == "newest" and meili_ids:
            from django.db.models import Case, When
            preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(meili_ids)])
            products_query = products_query.order_by(preserved_order)
        else:
            sort_map = {
                "newest": "-updated",
                "price_asc": "price",
                "price_desc": "-price",
                "name_asc": "name",
                "name_desc": "-name",
            }
            products_query = products_query.order_by(sort_map.get(sort, "-updated"))
        
        products_list = list(products_query)
        cache.set(query_cache_key, products_list, 600)

    # Пагінація: по 6 товарів на сторінку
    paginator = Paginator(products_list, 6)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Збереження GET-параметрів (фільтрів) для посилань пагінації
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(
            WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True)
        )
        
    discounted_products = cache.get_or_set(
        "discounted_products_hot",
        lambda: list(Product.objects.filter(available=True, discount_percent__gt=0).order_by("-discount_percent", "-updated")[:8]),
        600
    )

    top_picks = cache.get_or_set(
        "products_top_picks",
        lambda: list(Product.objects.filter(available=True).order_by("-updated")[:10]),
        600
    )

    promo_banners = cache.get_or_set(
        "active_promo_banners",
        lambda: list(PromoBanner.objects.filter(is_active=True).order_by('order', '-id')),
        600
    )

    trending_categories = cache.get_or_set(
        "trending_categories_active",
        lambda: list(TrendingCategory.objects.filter(is_active=True).prefetch_related('categories').order_by('order', 'id')),
        600
    )

    return render(request, 'products/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'wishlist_ids': wishlist_ids,
        'price_min': price_min or "",
        'price_max': price_max or "",
        'availability': availability,
        'sort': sort,
        'discounted_products': discounted_products,
        'top_picks': top_picks,
        'promo_banners': promo_banners,
        'trending_categories': trending_categories,
        'active_trending': active_trending,
        'query_string': query_string,
    })

# для додавання товару
@login_required
def product_add(request):
    if not request.user.is_staff:
        messages.error(request, "Лише адміністратор може додавати товари.")
        return redirect('products:product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.slug = slugify(product.name)
            product.owner = request.user
            product.save()
            messages.success(request, f"Товар '{product.name}' успішно додано.")
            return redirect('accounts:seller_dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'products/product/add.html', {'form': form})


@login_required
def product_edit(request, id):
    if not request.user.is_staff:
        messages.error(request, "Лише продавці мають право редагувати товари.")
        return redirect('products:product_list')
    
    product = get_object_or_404(Product, id=id)
    if product.owner != request.user and not request.user.is_superuser:
        messages.error(request, "Ви не є власником цього товару.")
        return redirect('accounts:seller_dashboard')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.slug = slugify(product.name)
            product.save()
            messages.success(request, f"Товар '{product.name}' успішно оновлено.")
            return redirect('accounts:seller_dashboard')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product/edit.html', {'form': form, 'product': product})


@login_required
def product_delete(request, id):
    if not request.user.is_staff:
        messages.error(request, "Лише продавці мають право видаляти товари.")
        return redirect('products:product_list')
        
    product = get_object_or_404(Product, id=id)
    if product.owner != request.user and not request.user.is_superuser:
        messages.error(request, "Ви не є власником цього товару.")
        return redirect('accounts:seller_dashboard')
        
    if request.method == 'POST':
        product.delete()
        messages.success(request, f"Товар '{product.name}' успішно видалено.")
        return redirect('accounts:seller_dashboard')
        
    return render(request, 'products/product/delete_confirm.html', {'product': product})

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    reviews = product.reviews.select_related("user")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]

    bought_together = Product.objects.filter(
        order_items__order__items__product=product,
        available=True
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


def about_us(request):
    return render(request, 'products/pages/about_us.html')


def warranty(request):
    return render(request, 'products/pages/warranty.html')


def contacts(request):
    return render(request, 'products/pages/contacts.html')



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


from django.http import JsonResponse
from django.urls import reverse

def product_search_ajax(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)

    cache_key = f"ajax_search_{q.lower()}"
    results = cache.get(cache_key)
    if results is None:
        from .search import search_products_meili
        meili_ids = search_products_meili(q, limit=5)
        if meili_ids is not None:
            if meili_ids:
                from django.db.models import Case, When
                preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(meili_ids)])
                products = Product.objects.filter(id__in=meili_ids, available=True).order_by(preserved_order)
            else:
                products = Product.objects.none()
        else:
            products = Product.objects.filter(available=True, name__icontains=q)[:5]
            
        results = []
        for p in products:
            results.append({
                'id': p.id,
                'name': p.name,
                'price': str(p.get_discounted_price()),
                'image': p.image.url if p.image else None,
                'url': reverse('products:product_detail', args=[p.id, p.slug])
            })
        cache.set(cache_key, results, 300)
    return JsonResponse(results, safe=False)


def compare_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    comparison = request.session.get('comparison', [])
    
    if product.id in comparison:
        comparison.remove(product.id)
        added = False
    else:
        comparison.append(product.id)
        added = True
        
    request.session['comparison'] = comparison
    request.session.modified = True
    
    return JsonResponse({
        'added': added,
        'count': len(comparison)
    })


def compare_list(request):
    comparison = request.session.get('comparison', [])
    products = Product.objects.filter(id__in=comparison, available=True)
    return render(request, 'products/product/comparison.html', {
        'products': products
    })