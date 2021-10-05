import django.core.validators as validators
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Название тега',
        max_length=200,
        unique=True,
    )
    color = models.CharField(
        'Цвет тега',
        max_length=30,
        unique=True,
    )
    slug = models.SlugField(
        'Slug',
        max_length=20,
        unique=True,
        db_index=True
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return f'<{self.pk}, {self.name[:50]}>'


class IngredientDescription(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=200,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=200,
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return self.name[:30]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
        db_index=True,
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
    )
    image = models.ImageField(
        upload_to='recipes/images',
        verbose_name='Изображение рецепта',
    )
    text = models.TextField('Описание рецепта')
    ingredients = models.ManyToManyField(
        to=IngredientDescription,
        through='IngredientQuantity'
    )
    tags = models.ManyToManyField(Tag)
    cooking_time = models.IntegerField(
        'Время готовки',
        validators=[
            validators.MinValueValidator(
                1, 'Минимальное значение для времени 1 минута.'
            ),
        ]
    )
    carts = models.ManyToManyField(
        to=User,
        through='Cart',
        related_name='recipes_in_cart'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return f'<№{self.pk}, {self.name[:50]}>'

    @admin.display(description='Добавили в избранное')
    def in_favorite_count(self):
        return self.favorites.count()


class IngredientQuantity(models.Model):
    recipe = models.ForeignKey(to=Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        to=IngredientDescription,
        on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        'Количество',
        validators=[
            validators.MinValueValidator(
                1, 'Минимальное количество ингредиента 1 ед.измерения'
            ),
        ]
    )

    class Meta:
        verbose_name = 'ингредиент рецепта с кол-вом'
        verbose_name_plural = 'ингредиенты рецепта с кол-вом'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'<{self.ingredient.name}, amount:{self.amount}>'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe_favorite'
            )
        ]

    def __str__(self):
        return f'<{self.pk}>'


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='customers'
    )
    recipe = models.ForeignKey(
        Recipe, related_name='in_cart',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe_cart'
            )
        ]

    def __str__(self):
        return f'<{self.pk}>'
