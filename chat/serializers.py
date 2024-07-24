from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Chat, Message
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from custom_user.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Converts User model instances to JSON format and vice versa.
    """

    class Meta:
        model = CustomUser
        fields = ['id',
                  'email',
                  'first_name',
                  'last_name'
                  ]


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
        ]


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


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'password')
        extra_kwargs = {'password': {'write_only': True}}  # why?

    def create(self, validated_data):
        user = CustomUser.objects.create_user(email=validated_data['email'], password=validated_data['password'])
        return user


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ResendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
