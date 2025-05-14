from django.urls import path
from . import views

urlpatterns = [
    path('', views.wedding_list, name='wedding_list'),
    path('create/', views.wedding_create, name='wedding_create'),
    path('<int:wedding_id>/', views.wedding_detail, name='wedding_detail'),
    path('<int:wedding_id>/edit/', views.wedding_edit, name='wedding_edit'),
    path('<int:wedding_id>/delete/', views.wedding_delete, name='wedding_delete'),
    path('<int:wedding_id>/team/', views.wedding_team, name='wedding_team'),
    path('<int:wedding_id>/theme/', views.wedding_theme, name='wedding_theme'),
    path('<int:wedding_id>/events/create/', views.wedding_event_create, name='wedding_event_create'),
    path('events/<int:event_id>/edit/', views.wedding_event_edit, name='wedding_event_edit'),
    path('events/<int:event_id>/delete/', views.wedding_event_delete, name='wedding_event_delete'),
]
