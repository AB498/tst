from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', views.wedding_list, name='wedding_guest_list'),
    path('list/', views.guest_list, name='guest_list'),
    path('create/', views.guest_create, name='guest_create'),
    path('<int:guest_id>/', views.guest_detail, name='guest_detail'),
    path('<int:guest_id>/edit/', views.guest_edit, name='guest_edit'),
    path('<int:guest_id>/delete/', views.guest_delete, name='guest_delete'),
    path('qr/<str:token>/', views.guest_qr_login, name='guest_qr_login'),
    path('checkin/', views.guest_checkin, name='guest_checkin'),
    path('invitation/', views.send_invitation, name='send_invitation'),
    # Redirect guest login to the unified login
    path('login/', lambda request: redirect('login'), name='guest_login'),
]
