from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('novaposhta/cities/', views.ajax_novaposhta_cities, name='novaposhta_cities'),
    path('novaposhta/branches/', views.ajax_novaposhta_branches, name='novaposhta_branches'),
    path('ukrposhta/cities/', views.ajax_ukrposhta_cities, name='ukrposhta_cities'),
    path('ukrposhta/branches/', views.ajax_ukrposhta_branches, name='ukrposhta_branches'),
    path('meest/cities/', views.ajax_meest_cities, name='meest_cities'),
    path('meest/branches/', views.ajax_meest_branches, name='meest_branches'),
]