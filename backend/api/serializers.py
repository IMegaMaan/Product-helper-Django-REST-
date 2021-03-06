from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from users.models import Subscribe  # noqa
from .models import (Cart, Favorite, IngredientDescription, IngredientQuantity,
                     Recipe, Tag)

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',)
        model = User

    def get_is_subscribed(self, obj) -> bool:
        subscribe = Subscribe.objects.filter(
            user=self.context['request'].user.id,
            author=obj,
        ).exists()

        return subscribe


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = IngredientDescription


class IngredientRecipeSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(source='ingredient.name', required=False)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', required=False
    )
    id = serializers.IntegerField(
        source='ingredient.id', required=True
    )
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = IngredientQuantity
        fields = ('id', 'amount', 'name', 'measurement_unit',)


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredientquantity_set', many=True, required=True
    )
    image = Base64ImageField()
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=False,
        queryset=User.objects.all(),
        default=CurrentUserDefault()
    )
    cooking_time = serializers.IntegerField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time',)
        model = Recipe

    def create(self, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_list = validated_data.pop('ingredientquantity_set')
        new_recipe = Recipe.objects.create(
            author=validated_data.pop('author'),
            name=validated_data.pop('name'),
            image=validated_data.pop('image'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time'),
        )
        # link tags
        new_recipe.tags.set(tags_list)
        new_recipe.save()
        # link ingredients
        new_recipe = self.add_ingredients(new_recipe, ingredients_list)

        return new_recipe

    def update(self, instance, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_list = validated_data.get('ingredientquantity_set', )
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        # can be empty
        instance.text = validated_data.pop('text', instance.text)
        instance.cooking_time = validated_data.pop(
            'cooking_time', instance.cooking_time)
        instance.save()
        # link tags
        instance.tags.clear()
        instance.tags.set(tags_list)
        instance.save()
        # link ingredients
        instance = self.add_ingredients(instance, ingredients_list, True)
        instance.save()
        return instance

    def add_ingredients(self, recipe, ingredients: list or tuple,
                        clear_ingredients: bool = False):
        if clear_ingredients:
            recipe.ingredients.clear()

        recipe.save()

        for ingredient in ingredients:
            ingredient_description = get_object_or_404(
                IngredientDescription, id=ingredient['ingredient']['id']
            )
            ingredient_quantity, created = (
                IngredientQuantity.objects.get_or_create(
                    ingredient=ingredient_description,
                    defaults={'amount': abs(ingredient['amount'])},
                    recipe=recipe,
                )
            )
            if not created:
                ingredient_quantity.amount += abs(ingredient['amount'])
                ingredient_quantity.save()
        recipe.save()
        return recipe

    def validate_cooking_time(self, value):
        if value < 0:
            raise serializers.ValidationError(
                '?????????? ?????????????? ???? ?????????? ???????? ??????????????????????????')
        return value

    def validate_tags(self, value):
        if len(value) <= 0:
            raise serializers.ValidationError(
                '???? ?????????????????? ???? ???????????? ????????')
        self.unique_validator(value)

        return value

    def validate_ingredients(self, value):
        if len(value) <= 0:
            raise serializers.ValidationError(
                '???? ?????????????????? ???? ???????????? ??????????????????????.')
        for ing in value:
            if ing['amount'] <= 0:
                raise serializers.ValidationError(
                    '???????????????????? ?? ?????????????????????? ???? ?????????? ???????? ??????????????????????????.')
        return value

    def unique_validator(self, value) -> bool:
        len_set_values = len(set(value))
        if len_set_values != len(value):
            raise serializers.ValidationError(
                '???????????????????????? ???????????????? ?? ????????.')
        return True


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        source='ingredientquantity_set', many=True
    )
    image = Base64ImageField()
    author = AuthorSerializer(default=CurrentUserDefault())
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time',)
        model = Recipe

    def get_is_favorited(self, obj):
        is_favorited = Favorite.objects.filter(
            user=self.context['request'].user.id,
            recipe=obj.id,
        ).exists()
        return is_favorited

    def get_is_in_shopping_cart(self, obj):
        is_in_shopping_cart = Cart.objects.filter(
            user=self.context['request'].user.id,
            recipe=obj.id,
        ).exists()
        return is_in_shopping_cart


class RecipeLinkedModelsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time',)
        model = Recipe
        ordering = ['id']
