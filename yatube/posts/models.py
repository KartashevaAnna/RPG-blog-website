from django.contrib.auth import get_user_model
from django.db import models
from core.models import CreatedModel

User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='group',
        null=True,
        blank=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=250,
        null=True,
        blank=True,
        unique=True,
    )
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Комментируемый пост',
        related_name='comments',
        help_text='Пост, который вы комментируете'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='following',
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Подписка',
        verbose_name_plural = 'Подписки',
        unique_together = ('user', 'author',)

class Visitor(models.Model):
    user = models.TextField(default=None)

    def __str__(self):
        return self.user


class Setting(models.Model):
    user = models.OneToOneField(Visitor, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    value = models.CharField(max_length=200)

    def __str__(self):
        return self.name
