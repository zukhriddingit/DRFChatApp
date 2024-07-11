from rest_framework import permissions
from chat.models import Chat, Message


class IsChatParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a chat to view it.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Chat):
            return request.user == obj.user1 or request.user == obj.user2
        elif isinstance(obj, Message):
            return request.user == obj.chat.user1 or request.user == obj.chat.user2
        return False


# class IsMessageAuthor(permissions.BasePermission):
#     """
#     Custom permission to only allow authors of a message to update or delete it.
#     """
#     def has_object_permission(self, request, view, obj):
#         return request.user == obj.author


# class IsAuthorOrReadOnly(permissions.BasePermission):
#     # Custom permission to only allow
#     def has_object_permission(self, request, view, obj):
#         if request.method in permissions.SAFE_METHODS:
#             return True
#
#         return obj.author == request.user
