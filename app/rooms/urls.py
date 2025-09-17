from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    # Vistas principales
    path('', views.rooms_view, name='list'),
    path('detail/<int:room_id>/', views.room_detail, name='detail'),
    path('create/', views.create_room, name='create'),
    path('edit/<int:room_id>/', views.edit_room, name='edit'),
    path('delete/<int:room_id>/', views.delete_room, name='delete'),
    path('status/<int:room_id>/', views.room_status_update, name='status_update'),
    path('statistics/', views.rooms_statistics, name='statistics'),
    
    # API endpoints para AJAX
    path('api/', views.rooms_api, name='api_list'),
    path('api/create/', views.create_room_api, name='api_create'),
    path('api/<int:room_id>/', views.update_room_api, name='api_update'),
    path('api/<int:room_id>/delete/', views.delete_room_api, name='api_delete'),
]