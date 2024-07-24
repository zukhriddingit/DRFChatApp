from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MessageViewSet, verify_code, register, login, resend_verification_code

router = DefaultRouter()
router.register('chats', ChatViewSet, basename='chat')
router.register('messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
    # path('chats/<int:chat_id>/send_email/', send_chat_email, name='send_chat_email'),
    # path('request-verification-code/', request_verification_code, name='request_verification_code'),
    path('verify-code/', verify_code, name='verify_code'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('resend-verification-code/', resend_verification_code, name='resend_verification_code')
]
