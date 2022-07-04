# Generated by Django 2.2.16 on 2022-07-04 07:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [
        ('posts', '0001_initial'),
        ('posts', '0002_auto_20220219_1552'),
        ('posts', '0003_auto_20220419_2108'),
        ('posts', '0004_auto_20220615_1521'),
        ('posts', '0005_auto_20220621_1259'),
        ('posts', '0006_comment'),
        ('posts', '0007_auto_20220624_1658'),
        ('posts', '0008_auto_20220628_1746'),
        ('posts', '0009_auto_20220628_1808'),
        ('posts', '0010_follow'),
        ('posts', '0011_auto_20220701_1100')
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                (
                    'id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID')
                ),
                ('title', models.CharField(max_length=200)),
                (
                    'slug', models.SlugField(
                        blank=True, max_length=250, null=True, unique=True
                    )
                ),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                (
                    'id', models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'text', models.TextField(
                        help_text='Введите текст поста',
                        verbose_name='Текст поста'
                    )
                ),
                (
                    'author', models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='posts',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Автор')
                ),
                (
                    'group',
                    models.ForeignKey(
                        blank=True,
                        help_text='Группа, к которой будет относиться пост',
                        null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name='group',
                        to='posts.Group',
                        verbose_name='Группа'
                    )
                ),
                (
                    'image',
                    models.ImageField(
                        blank=True,
                        upload_to='posts/',
                        verbose_name='Картинка'
                    )
                ),
                (
                    'created',
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name='Дата создания'
                    )
                ),
            ],
            options={
                'ordering': ['-created'],
                'verbose_name': 'Пост',
                'verbose_name_plural': 'Посты',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'text',
                    models.TextField(
                        help_text='Введите текст комментария',
                        verbose_name='Текст комментария'
                    )
                ),
                (
                    'created',
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name='Дата создания'
                    )
                ),
                (
                    'author', models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='comments',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Автор комментария'
                    )
                ),
                (
                    'post', models.ForeignKey(
                        help_text='Пост, который вы комментируете',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='comments',
                        to='posts.Post',
                        verbose_name='Комментируемый пост'
                    )
                ),
            ],
            options={
                'verbose_name': 'Комментарий',
                'verbose_name_plural': 'Комментарии',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'created', models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name='Дата создания'
                    )
                ),
                (
                    'author',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='following',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Автор'
                    )
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='follower',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Подписчик'
                    )
                ),
            ],
            options={
                'verbose_name': ('Подписка',),
                'verbose_name_plural': ('Подписки',),
                'ordering': ['-created'],
                'unique_together': {('user', 'author')},
            },
        ),
    ]