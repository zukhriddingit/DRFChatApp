from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Chat, Message
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Converts User model instances to JSON format and vice versa.
    """

    # User = get_user_model()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email']  # Fields to be included in the serialized output


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.
    Converts Message model instances to JSON format and vice versa.
    """
    author = UserSerializer(read_only=True)  # Nested serializer to include author details in the message

    class Meta:
        model = Message
        fields = [
            'id',
            'chat_id',
            'author',
            'content',
            'timestamp',
        ]  # Fields to be included in the serialized output


class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer for the Chat model.
    Converts Chat model instances to JSON format and vice versa.
    """
    user1 = UserSerializer(read_only=True)  # Nested serializer to include details of user1
    user2 = UserSerializer(read_only=True)  # Nested serializer to include details of user2
    last_message = serializers.SerializerMethodField()  # Custom field to include the last message in the chat

    class Meta:
        model = Chat
        fields = ['id', 'user1', 'user2', 'created_at',
                  'last_message']  # Fields to be included in the serialized output

    def get_last_message(self, obj):
        """
        Method to get the last message in the chat.
        """
        last_message = obj.messages.last()  # Retrieve the last message in the chat
        if last_message:
            return MessageSerializer(last_message).data  # Return the serialized last message
        return None  # Return None if there are no messages
