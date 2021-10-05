import csv

import django_filters.rest_framework
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from users.models import CustomUser, Subscribe # noqa
from .filters import RecipeFilter, CustomIngredientsFilter
from .models import (Cart, Favorite, IngredientDescription, IngredientQuantity,
                     Recipe, Tag)
from .paginators import CustomPagination
from .permissions import IsOwnerOrAcceptedMethods
from .serializers import (IngredientDescriptionSerializer,
                          RecipeCreateSerializer, RecipeLinkedModelsSerializer,
                          RecipeSerializer, TagSerializer)


class TagViewSet(ListAPIView, RetrieveAPIView, viewsets.GenericViewSet):
    """
    http://localhost/api/tags/ [GET]
    http://localhost/api/tags/{id} [GET]
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ListAPIView, RetrieveAPIView, viewsets.GenericViewSet):
    """
    http://localhost/api/tags/ [GET]
    url host:port/api/ingredients/{id}/ [GET]

    Filters:
    - Search filter:
        - name;
    """
    queryset = IngredientDescription.objects.all()
    serializer_class = IngredientDescriptionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = CustomIngredientsFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    url host:port/api/ingredients/
    Available methods:
    http://localhost/api/recipes/ [GET] - получение списка рецептов
    http://localhost/api/recipes/ [POST] - создание рецепта
    http://localhost/api/recipes/{id}/ [GET] - Получение рецепта
    http://localhost/api/recipes/{id}/ [PUT] - обновление рецепта
    http://localhost/api/recipes/{id}/ [DEL] - удаление рецепта

    Filters:
    - tags;
    - is_favorited;
    - author;
    - is_in_shopping_cart;
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = RecipeFilter
    pagination_class = CustomPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrAcceptedMethods,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def patch(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeCreateSerializer(
            recipe, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=201, data=serializer.data)
        return Response(status=400, data="wrong parameters")

    @action(detail=True, permission_classes=[permissions.IsAuthenticated],
            methods=['get', 'delete'])
    def shopping_cart(self, request, pk=None, model_name: str = 'cart'):
        kwargs = self.do_action_with_model(request, pk, model_name)
        return Response(**kwargs)

    @action(detail=True, permission_classes=[permissions.IsAuthenticated],
            methods=['get', 'delete'])
    def favorite(self, request, pk=None, model_name: str = 'favorite'):
        kwargs = self.do_action_with_model(request, pk, model_name)
        return Response(**kwargs)

    def do_action_with_model(self, request, pk: int, model_name: str):
        """
        this funtion may actions with some models
        :param request:
        :param pk: pk of Recipe model
        :param model_name: model name to actions with Recipe
        :return:
        """
        model = {
            'cart': Cart,
            'favorite': Favorite,
        }.get(model_name)

        if request.method == 'GET':
            kwargs = self.add_recipe_to_model(request, pk, model)  # noqa
            return kwargs
        elif request.method == 'DELETE':
            kwargs = self.delete_model_with_recipe(request, pk, model)  # noqa
            return kwargs

    def add_recipe_to_model(self, request, pk, model: Cart or Favorite):
        recipe = get_object_or_404(Recipe, pk=pk)
        new_model = model.objects.filter(
            recipe=recipe,
            user=request.user,
        )
        if new_model:
            return {'status': status.HTTP_400_BAD_REQUEST}
        model.objects.create(
            recipe=recipe,
            user=request.user,
        )
        serializer = RecipeLinkedModelsSerializer(recipe)
        return {'data': serializer.data, 'status': status.HTTP_200_OK}

    def delete_model_with_recipe(self, request, pk, model: Cart or Favorite):
        recipe = get_object_or_404(Recipe, pk=pk)
        model_with_recipe = model.objects.get(
            user=request.user,
            recipe=recipe
        )
        if not model_with_recipe:
            return status.HTTP_400_BAD_REQUEST
        model_with_recipe.delete()
        return {'status': status.HTTP_204_NO_CONTENT}

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user_cart = (
            Cart.objects.filter(user=request.user)
                .values_list('recipe', flat=True)
        )
        ingredients = (
            IngredientQuantity.objects.filter(recipe__id__in=user_cart)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amounts=Sum('amount')).all()
        )
        # Generate file
        response = HttpResponse(
            content_type='text/csv',
            headers={
                'Content-Disposition':
                    'attachment; filename="Список покупок.csv"'
            },
        )

        writer = csv.writer(response)
        for ing in ingredients:
            writer.writerow(
                [str(ing['ingredient__name']),
                 str(ing['amounts']),
                 str(ing['ingredient__measurement_unit'])]
            )
        return response
