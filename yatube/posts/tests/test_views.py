import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class UrlsMatchTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAnna')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='My test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_correct_template_used(self):
        cache.clear()
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (reverse('posts:posts_index'), 'posts/index.html'),
            (
                reverse(
                    'posts:profile', kwargs={'username': self.post.author}
                ),
                'posts/profile.html'
            ),
            (
                reverse(
                    'posts:post_detail', kwargs={'post_id': self.post.pk}
                ),
                'posts/post_detail.html'
            ),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (
                reverse(
                    'posts:post_edit', kwargs={'post_id': self.post.pk}
                ),
                'posts/create_post.html'
            ),
        )
        for reverse_name, template, in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsContextViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test user')
        cls.another_user = User.objects.create_user(username='AnotherUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Первый тестовый пост',
            group=cls.group,
            author=cls.user,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_shows_correct_context(self):
        cache.clear()
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:posts_index'))
        my_test_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context)
        self.assertEqual(my_test_object.text, 'Первый тестовый пост')
        self.assertEqual(my_test_object.group, self.post.group)
        self.assertEqual(my_test_object.author, self.user)
        self.assertIn(self.uploaded.name, my_test_object.image.name)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        my_test_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context)
        self.assertEqual(my_test_object.text, 'Первый тестовый пост')
        self.assertEqual(my_test_object.group, self.post.group)
        self.assertEqual(my_test_object.author, self.user)
        self.assertIn(self.uploaded.name, my_test_object.image.name)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        my_test_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context)
        self.assertEqual(my_test_object.text, 'Первый тестовый пост')
        self.assertEqual(my_test_object.group, self.post.group)
        self.assertEqual(my_test_object.author, self.user)
        self.assertNotIn(self.another_user, response.context['page_obj'])
        self.assertIn(self.uploaded.name, my_test_object.image.name)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        my_test_object = response.context['post']
        self.assertEqual(my_test_object.text, 'Первый тестовый пост')
        self.assertEqual(my_test_object.group, self.post.group)
        self.assertEqual(my_test_object.author, self.user)
        self.assertIn(self.uploaded.name, my_test_object.image.name)

    def correct_form_fields(self, response):
        """Поля формы PostForm работают корректно."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,

        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        self.correct_form_fields(response)
        self.assertEqual(response.context['post_id'], self.post.pk)

    def test_post_create_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.correct_form_fields(response)


class PaginationViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test user')
        cls.another_user = User.objects.create_user(username='AnotherUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        posts = [
            Post(
                text=f'Пост №{post_number}', author=cls.user,
                group=cls.group,
            ) for post_number in range(13)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_aggregate_pagination_test(self):
        """Пагинатор работает корректно"""
        max_per_page = 10
        total_posts = 13
        pagination = (
            (1, max_per_page),
            (2, total_posts - max_per_page)
        )
        my_urls = (
            reverse('posts:posts_index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for page, posts_count in pagination:
            for reverse_name in my_urls:
                response = self.authorized_client.get(
                    reverse_name,
                    {'page': page})
            self.assertEqual(
                len(response.context.get('page_obj').object_list), posts_count
            )


class CreatedPostDoesntFallInWrongGroup(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AnnaTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.another_group = Group.objects.create(
            title='Вторая тестовая группа',
            slug='another_group',
            description='Вторая группа, чтобы проверить фильтрацию по группе'
        )
        cls.post = Post.objects.create(
            text='My test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_extra_check_for_post_creation(self):
        cache.clear()
        """Дополнительная проверка при создании поста."""
        Post.objects.create(
            text='Дополнительное тестирование',
            author=self.user,
            group=self.another_group,
        )
        my_urls = (
            reverse('posts:posts_index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.another_group.slug}
            ),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for reverse_name in my_urls:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                my_test_object = response.context['page_obj'][0]
                self.assertEqual(
                    my_test_object.text,
                    'Дополнительное тестирование'
                )
                self.assertEqual(my_test_object.group, self.another_group)
                self.assertEqual(my_test_object.author, self.user)

    def test_my_post_is_not_in_a_wrong_group(self):
        """Пост не попадает не в ту группу."""
        Post.objects.create(
            text='Дополнительное тестирование',
            author=self.user,
            group=self.another_group,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            )
        )
        my_test_object = response.context['page_obj']
        self.assertNotIn(
            'Дополнительное тестирование',
            my_test_object,
            'Post is in the wrong group'
        )


class CasheTestView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AnnaTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self) -> None:
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def post_created_with_first_cashe(self):
        my_new_post = Post.objects.create(
            text='Тестирую кеш',
            author=self.user,
            group=self.group,
        )
        content_with_post = self.authorized_client.get(
            reverse('posts:posts_index')
        ).content
        my_new_post.delete()
        return my_new_post, content_with_post

    def test_post_is_cached(self):
        """Тестируем работу кеша."""
        my_new_post, content_with_post = self.post_created_with_first_cashe()
        content_with_cashed_post = self.authorized_client.get(
            reverse('posts:posts_index')
        ).content
        self.assertEqual(content_with_post, content_with_cashed_post)

    def test_post_deleted_cache_cleared(self):
        my_new_post, content_with_post = self.post_created_with_first_cashe()
        cache.clear()
        content_post_deleted_cash_cleared = self.authorized_client.get(
            reverse('posts:posts_index')
        ).content
        self.assertNotEqual(
            content_with_post, content_post_deleted_cash_cleared
        )


class FollowingTestView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AnnaTest')
        cls.another_user = User.objects.create_user(username='George')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post_by_author = Post.objects.create(
            text='Подписка',
            author=cls.another_user,
            group=cls.group,
        )
        cls.post_by_user = Post.objects.create(
            text='Hello, World!',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self) -> None:
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.another_user)

    def get_posts_by_followed_author(self):
        self.author = self.another_user
        followed_posts = Post.objects.filter(
            author__following__user=self.user
        )
        return followed_posts

    def test_profile_follow(self):
        Follow.objects.all().delete()
        """Проверяем, что пост возникает на странице подписки."""
        post_list_before = list(self.get_posts_by_followed_author())
        post_list_before_count = self.get_posts_by_followed_author().count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.another_user.username}
            )
        )
        post_list_after = list(self.get_posts_by_followed_author())
        post_list_after_count = self.get_posts_by_followed_author().count()
        with self.subTest():
            self.assertEqual(
                post_list_before_count + 1,
                post_list_after_count
            )
            self.assertNotIn(self.post_by_author, post_list_before)
            self.assertIn(self.post_by_author, post_list_after)
            self.assertNotIn(self.post_by_user, post_list_after)

    def test_profile_unfollow(self):
        """Проверяем, что подписка удаляется из базы данных."""
        Follow.objects.create(
            user=self.user,
            author=self.another_user,
        )
        post_list_before = list(self.get_posts_by_followed_author())
        post_list_before_count = self.get_posts_by_followed_author().count()
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.another_user.username}
            )
        )
        post_list_after = list(self.get_posts_by_followed_author())
        post_list_after_count = self.get_posts_by_followed_author().count()
        with self.subTest():
            self.assertEqual(post_list_before_count, post_list_after_count + 1)
            self.assertIn(self.post_by_author, post_list_before)
            self.assertNotIn(self.post_by_author, post_list_after)
