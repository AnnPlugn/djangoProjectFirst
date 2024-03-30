from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    """"данные о записи"""
    title = models.CharField('Заголовок записи', max_length=100)
    description = models.TextField('Текст записи')
    author = models.CharField('Имя автора', max_length=100)
    date = models.DateField('Дата публикации')

    def __str__(self):
        return f'{self.title},{self.author}'

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'

