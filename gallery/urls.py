from django.urls import path
from . import views

urlpatterns = [
    path('', views.wedding_list, name='wedding_gallery_list'),
    path('list/', views.gallery_list, name='gallery_list'),
    path('upload/', views.gallery_upload, name='gallery_upload'),
    path('<int:media_id>/', views.media_detail, name='media_detail'),
    path('<int:media_id>/delete/', views.media_delete, name='media_delete'),
    path('wedding/<int:wedding_id>/', views.wedding_gallery, name='wedding_gallery'),
    path('wedding/<int:wedding_id>/guests/', views.guest_gallery, name='guest_gallery'),
    path('wedding/<int:wedding_id>/guests/<int:guest_id>/', views.guest_gallery, name='guest_gallery_detail'),
    path('wedding/<int:wedding_id>/settings/', views.gallery_settings, name='gallery_settings'),
    path('invite/<uuid:token>/', views.gallery_invite, name='gallery_invite'),
    path('public/<int:wedding_id>/', views.public_gallery, name='public_gallery'),
]
