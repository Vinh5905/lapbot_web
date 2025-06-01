from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path("", views.index, name="index"), # URL cho trang chat chính
    path('send_message/', views.send_message, name='send_message'), # URL để xử lý việc gửi tin nhắn từ client (sử dụng AJAX),
    path('intent_detect/', views.intent_detect, name='intent_detect')
]