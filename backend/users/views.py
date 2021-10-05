from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.paginators import CustomPagination  # noqa
from api.serializers import AuthorSerializer  # noqa
from .models import CustomUser, Subscribe
from .serializers import SubscribeListSerializer, UserCreateSerializer


class UserSet(mixins.ListModelMixin,
              mixins.CreateModelMixin,
              viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in {'create'}:
            return UserCreateSerializer
        return AuthorSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return get_object_or_404(CustomUser, id=user_id)
        queryset = CustomUser.objects.all()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if isinstance(queryset, CustomUser):
            serializer = self.get_serializer(queryset)
            return JsonResponse(serializer.data)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data)

    @action(detail=True, permission_classes=[permissions.IsAuthenticated],
            methods=['delete', 'get'])
    def subscribe(self, request, pk=None):
        if request.method == 'DELETE':
            kwargs = self.delete_subscribe(request, pk)
            return Response(**kwargs)

        elif request.method == 'GET':
            kwargs = self.create_subscribe(request, pk)
            return Response(**kwargs)

    def create_subscribe(self, request, author_id: int) -> dict:
        author = get_object_or_404(CustomUser, pk=author_id)
        subscribe = Subscribe.objects.filter(
            author=author,
            user=request.user,
        )
        if subscribe or author_id == request.user.pk:
            return {
                'data': {'error_400': 'Ошибка подписки'},
                'status': status.HTTP_400_BAD_REQUEST,
            }
        new_subscribe = Subscribe.objects.create(
            author=author,
            user=request.user,
        )
        serializer = SubscribeListSerializer(new_subscribe)
        return {'data': serializer.data, 'status': status.HTTP_200_OK}

    def delete_subscribe(self, request, pk) -> dict:
        if pk == request.user.id:
            return {'status': status.HTTP_400_BAD_REQUEST}
        subscribe = get_object_or_404(
            Subscribe, author=pk, user=request.user.id)
        subscribe.delete()
        return {'status': status.HTTP_204_NO_CONTENT}


class SubscriptionsListSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    url http://localhost/api/users/subscriptions/ [GET]
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SubscribeListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Subscribe.objects.filter(user=self.request.user)
        return queryset
