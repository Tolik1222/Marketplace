from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from .cart import Cart
from .forms import CouponApplyForm
from orders.models import Coupon
from django.utils import timezone

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'cart_count': len(cart)})
    return redirect('cart:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart, 'coupon_apply_form': CouponApplyForm()})


@require_POST
def cart_apply_coupon(request):
    now = timezone.now()
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data["code"]
        coupon = Coupon.objects.filter(code__iexact=code, active=True, valid_from__lte=now, valid_to__gte=now).first()
        if coupon:
            request.session["coupon_id"] = coupon.id
            messages.success(request, f"Промокод {coupon.code} застосовано.")
        else:
            request.session["coupon_id"] = None
            messages.error(request, "Промокод не знайдено або він неактивний.")
    return redirect('cart:cart_detail')
