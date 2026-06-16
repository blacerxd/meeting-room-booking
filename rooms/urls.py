from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('scanner/', views.qr_scanner, name='scanner'),
    path('process_qr/', views.process_qr_code, name='process_qr'),
    path('exit/<int:entry_id>/', views.exit_room, name='exit_room'),
    path('list/', views.room_list, name='room_list'),
    path('<int:room_id>/', views.room_detail, name='room_detail'),
    path('api/entries/', views.user_entries_api, name='entries_api'),
]
