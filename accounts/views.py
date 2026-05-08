from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from products.models import Product
from orders.models import Order


def register(request):
    """Реєстрація нового користувача"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Вітаємо! Ви успішно зареєструвались.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки в формі.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """Вхід користувача"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Вітаємо, {user.username}!')
                
                # Перенаправлення на попередню сторінку або на профіль
                next_page = request.GET.get('next', 'accounts:profile')
                return redirect(next_page)
        else:
            messages.error(request, 'Невірне ім\'я користувача або пароль.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """Вихід користувача"""
    logout(request)
    messages.info(request, 'Ви успішно вийшли з системи.')
    return redirect('products:product_list')


@login_required
def profile(request):
    """Особистий кабінет користувача"""
    user_products = Product.objects.filter(owner=request.user) if hasattr(Product, "owner") else Product.objects.none()
    user_orders = (
        Order.objects.filter(Q(user=request.user) | Q(user__isnull=True, email=request.user.email))
        .prefetch_related("items__product")
        .order_by("-created")
        .distinct()
    )

    context = {
        "user_products": user_products,
        "user_orders": user_orders,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Редагування профілю"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})