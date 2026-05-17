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
    path('edit/<int:id>/', views.product_edit, name='product_edit'),
    path('delete/<int:id>/', views.product_delete, name='product_delete'),
    path('compare/toggle/<int:product_id>/', views.compare_toggle, name='compare_toggle'),
    path('compare/', views.compare_list, name='compare_list'),
    path('search/ajax/', views.product_search_ajax, name='product_search_ajax'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
]