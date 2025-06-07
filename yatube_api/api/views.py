from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import ValidationError, NotAuthenticated
from django.shortcuts import get_object_or_404

from .serializers import (
    FollowSerializer,
    PostSerializer,
    CommentSerializer,
    GroupSerializer
)
from .permissions import IsAuthorOrReadOnly
from posts.models import Follow, Post, Group


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Анонимный запрос запрещен')
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    lookup_field = 'id'

    def get_post(self):
        return get_object_or_404(Post, id=self.kwargs['post_id'])

    def get_queryset(self):
        return self.get_post().comments.all()

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Анонимный запрос запрещен')
        serializer.save(author=self.request.user, post=self.get_post())


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('following__username',)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        following = serializer.validated_data['following']
        if user == following:
            raise ValidationError('Невозможно подписаться на самого себя!')
        if Follow.objects.filter(user=user, following=following).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя')
        serializer.save(user=user)
