from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/dashboard/export/', views.seller_export_excel, name='seller_export_excel'),
    path('seller/profile/', views.seller_profile_edit, name='seller_profile_edit'),
    path('seller/orders/<int:sub_order_id>/', views.seller_suborder_detail, name='seller_suborder_detail'),
    path('seller/orders/<int:sub_order_id>/generate-ttn/', views.generate_novaposhta_waybill, name='generate_novaposhta_waybill'),
]