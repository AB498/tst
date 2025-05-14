from django.urls import path
from . import views

urlpatterns = [
    # Task URLs
    path('', views.wedding_list, name='wedding_task_list'),
    path('list/', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
    path('<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('<int:task_id>/complete/', views.task_complete, name='task_complete'),

    # Checklist URLs
    path('checklist/', views.checklist, name='checklist'),
    path('checklist/create/', views.checklist_create, name='checklist_create'),
    path('checklist/<int:checklist_id>/', views.checklist_detail, name='checklist_detail'),
    path('checklist/<int:checklist_id>/edit/', views.checklist_edit, name='checklist_edit'),
    path('checklist/<int:checklist_id>/delete/', views.checklist_delete, name='checklist_delete'),
    path('checklist/item/<int:item_id>/toggle/', views.checklist_item_toggle, name='checklist_item_toggle'),
    path('checklist/template/<int:template_id>/use/', views.use_template, name='use_template'),

    # Reminder URLs
    path('reminders/', views.reminders, name='reminders'),
]
