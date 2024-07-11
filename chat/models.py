from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
"""
Chat model. Has 2 users, user1 and user2 from User model. Also has created_at date-time field. __str__ method
changed to returning users usernames.
"""


class Chat(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_as_user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat between {self.user1.email} and {self.user2.email}"


"""
Message model. Has chat to which the message belongs to, author of the message, content of the message
and the timestamp. Ordering is set to date-time ordering.
"""


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "hi"
        # return f"Message from {self.author.username} in chat {self.chat.id}"

    class Meta:
        ordering = ['timestamp']
