import logging

from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse 
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.conf import settings
from django.core.cache import cache
import requests
import re
from .tasks import send_order_notifications_task

logger = logging.getLogger(__name__)


def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    has_expensive_item = any(item['product'].price > 10000 for item in cart)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST, has_expensive_item=has_expensive_item)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                coupon = cart.get_coupon()
                if coupon and coupon.is_valid():
                    order.coupon = coupon
                    order.discount = coupon.discount
                order.save()
                from collections import defaultdict
                from .models import SubOrder
                items_by_vendor = defaultdict(list)
                for item in cart:
                    vendor = item['product'].owner
                    items_by_vendor[vendor].append(item)
                
                for vendor, vendor_items in items_by_vendor.items():
                    sub_order = SubOrder.objects.create(
                        order=order,
                        vendor=vendor,
                        status='pending'
                    )
                    for item in vendor_items:
                        OrderItem.objects.create(
                            order=order,
                            sub_order=sub_order,
                            product=item['product'],
                            price=item['price'],
                            quantity=item['quantity'],
                        )
            
            request.session['order_id'] = order.id
            # Send notifications asynchronously using Celery
            send_order_notifications_task.delay(order.id)
            cart.clear()
            
            if order.payment_method == 'cod':
                return redirect(reverse('payment:completed'))
            return redirect(reverse('payment:process'))
            
    else:
        form = OrderCreateForm(has_expensive_item=has_expensive_item)
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})


from django.http import JsonResponse

def transliterate_latin_to_cyrillic(text):
    common_cities = {
        'kyiv': 'Київ',
        'kiev': 'Київ',
        'kharkiv': 'Харків',
        'kharkov': 'Харків',
        'dnipro': 'Дніпро',
        'dnepr': 'Дніпро',
        'odesa': 'Одеса',
        'odessa': 'Одеса',
        'lviv': 'Львів',
        'lvov': 'Львів',
        'zaporizhzhia': 'Запоріжжя',
        'zaporozhye': 'Запоріжжя',
        'sumy': 'Суми',
        'poltava': 'Полтава',
        'chernihiv': 'Чернігів',
        'chernigov': 'Чернігів',
        'cherkasy': 'Черкаси',
        'cherkassy': 'Черкаси',
        'vinnytsia': 'Вінниця',
        'vinnitsa': 'Вінниця',
        'kherson': 'Херсон',
        'zhytomyr': 'Житомир',
        'shitomir': 'Житомир',
        'khmelnytskyi': 'Хмельницький',
        'khmelnitsky': 'Хмельницький',
        'chernivtsi': 'Чернівці',
        'chernovtsy': 'Чернівці',
        'rivne': 'Рівне',
        'rovno': 'Рівне',
        'kamianske': 'Кам\'янське',
        'kremenchuk': 'Кременчук',
        'lutsk': 'Луцьк',
        'ternopil': 'Тернопіль',
        'kropyvnytskyi': 'Кропивницький',
        'krasnograd': 'Красноград',
        'uzhhorod': 'Ужгород',
        'uzhgorod': 'Ужгород',
    }
    query_lower = text.lower().strip()
    if query_lower in common_cities:
        return common_cities[query_lower]
    rules = {
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'ye': 'є', 'zh': 'ж', 'z': 'з',
        'i': 'і', 'yi': 'ї', 'y': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
        'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'kh': 'х', 'ts': 'ц', 'ch': 'ч',
        'sh': 'ш', 'shch': 'щ', 'yu': 'ю', 'ya': 'я', 'h': 'г', 'c': 'ц', 'w': 'в', 'x': 'кс',
    }
    sorted_keys = sorted(rules.keys(), key=len, reverse=True)
    res = query_lower
    for k in sorted_keys:
        res = res.replace(k, rules[k])
    return res.capitalize()

def ajax_novaposhta_cities(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    if re.search(r'[a-zA-Z]', q):
        q = transliterate_latin_to_cyrillic(q)
    
    cache_key = f"novaposhta_cities_{q.lower()}"
    cached_cities = cache.get(cache_key)
    if cached_cities is not None:
        return JsonResponse(cached_cities, safe=False)
    
    fallback_cities = [
        {'name': 'Київ', 'ref': 'db5c88f5-391c-11dd-90d9-001a4d12cfd8'},
        {'name': 'Харків', 'ref': 'db5c88f0-391c-11dd-90d9-001a4d12cfd8'},
        {'name': 'Дніпро', 'ref': 'db5c88ee-391c-11dd-90d9-001a4d12cfd8'},
        {'name': 'Одеса', 'ref': 'db5c88f2-391c-11dd-90d9-001a4d12cfd8'},
        {'name': 'Львів', 'ref': 'db5c88f3-391c-11dd-90d9-001a4d12cfd8'},
        {'name': 'Запоріжжя', 'ref': 'db5c88f7-391c-11dd-90d9-001a4d12cfd8'},
        {'name': 'Івано-Франківськ', 'ref': 'db5c88f1-391c-11dd-90d9-001a4d12cfd8'},
    ]
    
    try:
        payload = {
            "apiKey": "",
            "modelName": "Address",
            "calledMethod": "getCities",
            "methodProperties": {
                "FindByString": q,
                "Limit": "10"
            }
        }
        res = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data.get('success'):
                cities = []
                for item in data.get('data', []):
                    cities.append({
                        'name': item.get('Description', ''),
                        'ref': item.get('Ref', '')
                    })
                if cities:
                    cache.set(cache_key, cities, 86400)  # cache for 24 hours
                    return JsonResponse(cities, safe=False)
    except Exception as e:
        logger.error(f"Nova Poshta Cities API error: {e}")
        
    filtered_fallback = [c for c in fallback_cities if q.lower() in c['name'].lower()]
    return JsonResponse(filtered_fallback, safe=False)


def ajax_novaposhta_branches(request):
    city_ref = request.GET.get('city_ref', '').strip()
    if not city_ref:
        return JsonResponse([], safe=False)
        
    cache_key = f"novaposhta_branches_{city_ref}"
    cached_branches = cache.get(cache_key)
    if cached_branches is not None:
        return JsonResponse(cached_branches, safe=False)
        
    try:
        payload = {
            "apiKey": "",
            "modelName": "Address",
            "calledMethod": "getWarehouses",
            "methodProperties": {
                "CityRef": city_ref,
                "Limit": "50"
            }
        }
        res = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data.get('success'):
                branches = []
                for item in data.get('data', []):
                    branches.append({
                        'name': item.get('Description', ''),
                        'ref': item.get('Ref', '')
                    })
                if branches:
                    cache.set(cache_key, branches, 86400)  # cache for 24 hours
                    return JsonResponse(branches, safe=False)
    except Exception as e:
        logger.error(f"Nova Poshta Branches API error: {e}")
        
    fallback_branches = [
        {'name': 'Відділення №1: вул. Пироговський шлях, 135', 'ref': 'fallback-1'},
        {'name': 'Відділення №2: вул. Сирецька, 9', 'ref': 'fallback-2'},
        {'name': 'Відділення №3: вул. Калачівська, 13', 'ref': 'fallback-3'},
    ]
    return JsonResponse(fallback_branches, safe=False)


def ajax_ukrposhta_cities(request):
    return ajax_novaposhta_cities(request)


def ajax_meest_cities(request):
    return ajax_novaposhta_cities(request)


def ajax_ukrposhta_branches(request):
    return JsonResponse([
        {'name': 'Головне відділення Укрпошти №1 (вул. Хрещатик, 22)', 'ref': 'ukr-1'},
        {'name': 'Відділення №2 (вул. Соборна, 15)', 'ref': 'ukr-2'},
        {'name': 'Відділення №3 (просп. Перемоги, 120)', 'ref': 'ukr-3'},
        {'name': 'Відділення №4 (вул. Шевченка, 44)', 'ref': 'ukr-4'},
        {'name': 'Відділення №5 (вул. Франка, 8)', 'ref': 'ukr-5'},
    ], safe=False)


def ajax_meest_branches(request):
    return JsonResponse([
        {'name': 'Міні-відділення Meest №125 (супермаркет "Сільпо", вул. Басейна, 12)', 'ref': 'meest-1'},
        {'name': 'Відділення №301 (вул. Шевченка, 88)', 'ref': 'meest-2'},
        {'name': 'Поштомат Meest №3020 (вул. Перемоги, 4)', 'ref': 'meest-3'},
        {'name': 'Поштомат Meest №3114 (вул. Франка, 35)', 'ref': 'meest-4'},
    ], safe=False)