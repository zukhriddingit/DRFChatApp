from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Chat, Message

class ChatAppTests(APITestCase):

    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

        # Create a chat between user1 and user2
        self.chat = Chat.objects.create(user1=self.user1, user2=self.user2)

        # Create messages
        self.message1 = Message.objects.create(chat=self.chat, author=self.user1, content="Hello User2")
        self.message2 = Message.objects.create(chat=self.chat, author=self.user2, content="Hello User1")

        # Generate JWT token for user1
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)

    def test_user_can_see_own_chats(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get('/api/chats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.chat.id)

    def test_user_can_see_messages_in_chat(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(f'/api/chats/{self.chat.id}/messages/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_user_can_send_message(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post('/api/messages/', {'chat': self.chat.id, 'content': 'New message'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.count(), 3)

    def test_user_can_update_own_message(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.put(f'/api/messages/{self.message1.id}/', {'chat': self.chat.id, 'content': 'Updated message'})
        self.assertEqual(response.status_code, 200)
        self.message1.refresh_from_db()
        self.assertEqual(self.message1.content, 'Updated message')

    def test_user_cannot_update_others_message(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.put(f'/api/messages/{self.message2.id}/', {'chat': self.chat.id, 'content': 'Updated message'})
        self.assertEqual(response.status_code, 403)

    def test_user_can_delete_own_message(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.delete(f'/api/messages/{self.message1.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Message.objects.count(), 1)

    def test_user_cannot_delete_others_message(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.delete(f'/api/messages/{self.message2.id}/')
        self.assertEqual(response.status_code, 403)
