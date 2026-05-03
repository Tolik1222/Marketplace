from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('shipping-payment/', views.shipping_payment, name='shipping_payment'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('review/<int:product_id>/', views.review_create, name='review_create'),
    path('add/', views.product_add, name='product_add'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
]