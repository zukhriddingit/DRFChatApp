import random
import threading
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as djfilters
from .models import Chat, Message
from .serializers import UserSerializer, ChatSerializer, MessageSerializer, RegisterSerializer, VerifyCodeSerializer, \
    LoginSerializer, ResendVerificationCodeSerializer
from .permissions import IsChatParticipant
from .utils import send_chat_message_email, generate_verification_code, \
    store_verification_code, redis_client
from custom_user.models import CustomUser
from .tasks import send_verification_email


class ChatFilter(djfilters.FilterSet):
    user1_id = djfilters.NumberFilter(field_name="user1__id")
    user2_id = djfilters.NumberFilter(field_name="user2__id")

    class Meta:
        model = Chat
        fields = ['user1_id', 'user2_id', 'created_at']


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated, IsChatParticipant]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filterset_fields = ['user1_id', 'user2_id', 'created_at']
    filterset_class = ChatFilter
    search_fields = ['user1__email', 'user2__email']
    ordering_fields = ['created_at', 'id']

    def get_queryset(self):
        # Override the default queryset to return only chats that the requesting user is a participant of.
        user_id = self.request.user.id
        return Chat.objects.filter(user1_id=user_id).select_related('user1', 'user2') | Chat.objects.filter(
            user2_id=user_id).select_related('user1', 'user2')

    def perform_create(self, serializer):
        # Override the perform_create method to save a new chat with the authenticated user and another specified user.
        user1 = self.request.user
        user2_email = self.request.data.get('user2')
        user2 = User.objects.get(email=user2_email)
        serializer.save(user1=user1, user2=user2)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def messages(self, request, pk=None):
        # Custom action to handle messages within a chat.
        chat = self.get_object()
        if request.method == 'GET':
            messages = Message.objects.select_related('author').filter(chat=chat)
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = MessageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user, chat=chat)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated, IsMessageAuthor])
    # def update_message(self, request, pk=None):
    #     """
    #     Custom action to update a message in a chat.
    #     """
    #     message = Message.objects.get(pk=request.data.get('message_id'))
    #     if message.author != request.user:
    #         return Response({"detail": "You do not have permission to edit this message."}, status=status.HTTP_403_FORBIDDEN)
    #
    #     serializer = MessageSerializer(message, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #
    # @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated, IsMessageAuthor])
    # def delete_message(self, request, pk=None):
    #     """
    #     Custom action to delete a message in a chat.
    #     """
    #     message = Message.objects.get(pk=request.data.get('message_id'))
    #     if message.author != request.user:
    #         return Response({"detail": "You do not have permission to delete this message."}, status=status.HTTP_403_FORBIDDEN)
    #
    #     message.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class MessageFilter(djfilters.FilterSet):
    chat_id = djfilters.NumberFilter(field_name="chat__id")
    author_id = djfilters.NumberFilter(field_name="author__id")

    class Meta:
        model = Message
        fields = ['chat_id', 'author_id', 'timestamp']


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related('author', 'chat__user1', 'chat__user2')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MessageFilter
    # filterset_fields = ['chat_id', 'author_id', 'timestamp']
    search_fields = ['content']
    ordering_fields = ['timestamp', 'id']

    def get_queryset(self):
        # Override the default queryset to return only messages authored by the requesting user.
        return self.queryset.filter(author_id=self.request.user.id)

    def perform_create(self, serializer):
        # Override the perform_create method to save a new message with the authenticated user as the author.
        author = self.request.user
        chat_id = self.request.data.get('chat')
        chat = Chat.objects.get(id=chat_id)
        serializer.save(author=author, chat=chat)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    serializer = VerifyCodeSerializer(data=request.data)
    # email = request.data.get('email')
    # code = request.data.get('code')

    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        stored_code = redis_client.get(f'verification_code:{email}')
        # if not email or not code:
        #     return Response({"detail": "Email and verification code are required."}, status=status.HTTP_400_BAD_REQUEST)

        if stored_code and stored_code.decode('utf-8') == code:
            user = CustomUser.objects.get(email=email)
            user.is_active = True
            user.save()
            redis_client.delete(f"verification_code:{email}")
            return Response({'detail': 'Email verified successfully'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid or expired verification code'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    # email = request.data.get('email')
    # password = request.data.get('password')  # use serializers to do this
    serializer = RegisterSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    user = serializer.save(is_active=False)
    code = generate_verification_code()
    if not user.email or not user.password:
        return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    # store_verification_code(user.email, code)
    # send_verification_email(user.email, code)  # should run in another thread

    # threading
    # t1 = threading.Thread(target=store_verification_code, args=(user.email, code))
    # t2 = threading.Thread(target=send_verification_email, args=(user.email, code))
    # t1.start()
    # t2.start()

    # celery background task for email, not threading.
    # celery:
    send_verification_email.delay(user.email, code)
    # use docker desktop - Can't run docker desktop because my Ubuntu 24.04 LTS won't support it.
    return Response(
        {
            "detail": "User registered. Please verify your email to activate your account"
        }, status=status.HTTP_201_CREATED)
# use docker desktop, so you don't have to stop redis and postgresql to run docker.


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        # email = request.data.get('email')
        # password = request.data.get('password')
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)

        if user is not None:
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response({"detail": "Email not verified"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    serializer = ResendVerificationCodeSerializer(data=request.data)
    # email = request.data.get('email')
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            code = generate_verification_code()
            store_verification_code(email, code)
            send_verification_email.delay(email, code)
            return Response({'detail': 'New verification code sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def send_chat_email(request, chat_id):
#     user = request.user
#     try:
#         chat = Chat.objects.get(id=chat_id)
#         if user not in [chat.user1, chat.user2]:
#             return Response({"detail": "You do not have permission to view this chat."},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         messages = Message.objects.filter(chat=chat).order_by('timestamp')
#         message_texts = "\n".join([f"{msg.author.email}: {msg.content}" for msg in messages])
#
#         subject = f"Chat messages between {chat.user1.email} and {chat.user2.email}"
#         send_chat_message_email(user.email, subject, message_texts)
#
#         return Response({"detail": "Email sent successfully."}, status=status.HTTP_200_OK)
#     except Chat.DoesNotExist:
#         return Response({"detail": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
