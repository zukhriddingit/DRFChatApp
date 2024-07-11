from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MessageViewSet, send_chat_email

router = DefaultRouter()
router.register('chats', ChatViewSet, basename='chat')
router.register('messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
    path('chats/<int:chat_id>/send_email/', send_chat_email, name='send_chat_email')
]
