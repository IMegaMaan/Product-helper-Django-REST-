from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.serializers import RecipeLinkedModelsSerializer  # noqa
from .models import CustomUser


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password',
        )
        model = CustomUser
        extra_kwargs = {
            'email': {'required': True,
                      'validators': [
                          UniqueValidator(queryset=CustomUser.objects.all())
                      ]
                      },
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'required': True, 'write_only': True},
        }

    def create(self, validated_data) -> CustomUser:
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail("cannot_create_user")
        return user

    def perform_create(self, validated_data) -> CustomUser:
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                is_active=True, **validated_data)
        return user


class SubscribeListSerializer(serializers.Serializer):  # noqa
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = True
    recipes = serializers.SerializerMethodField('get_recipes', read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    def get_recipes_count(self, obj) -> int:
        return obj.author.recipes.count()

    def get_recipes(self, obj) -> dict:
        recipes_limit = (
            self.context['view'].request.query_params.get('recipes_limit')
            if self.context else None
        )
        recipes = (obj.author.recipes.all()[:int(recipes_limit)]
                   if recipes_limit
                   else obj.author.recipes.all())
        serializer = RecipeLinkedModelsSerializer(instance=recipes, many=True)
        return serializer.data
