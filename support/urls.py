from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("new/", views.ticket_create, name="ticket_create"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("<int:ticket_id>/status/", views.ticket_update_status, name="ticket_update_status"),
    path("<int:ticket_id>/messages/", views.ticket_messages_api, name="ticket_messages_api"),
]
