from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    password = models.CharField(
        'Пароль', null=False, blank=False, max_length=150
    )
    email = models.EmailField(
        'Почта', unique=True, blank=False, null=False, max_length=254)
    username = models.CharField(
        verbose_name='Никнейм', blank=True, unique=True, max_length=150)
    first_name = models.CharField(
        verbose_name='Имя', null=False,
        blank=False, max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия', null=False,
        blank=False, max_length=150
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField('Персонал сайта', default=False)
    date_joined = models.DateTimeField(
        'Дата создания пользователя', default=timezone.now)

    REQUIRED_FIELDS = (
        'username', 'password', 'first_name', 'last_name',
    )
    USERNAME_FIELD = 'email'

    objects = CustomUserManager()

    class Meta:
        ordering = ['pk']
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class Subscribe(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name="follower", verbose_name='Кто подписывается'
    )
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name="following", verbose_name='На кого подписаться'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'

    def __str__(self):
        return (f'Follower: {self.user.username} '  # noqa
                f'Following: {self.author.username}')  # noqa
