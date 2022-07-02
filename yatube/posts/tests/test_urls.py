from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class StaticUrlTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get(reverse('posts:posts_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PageAvailableTest(TestCase):
    """Проверяем, что страницы видны согласно правам доступа."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.my_author = Client()
        self.my_author.force_login(self.post.author)

    def test_available_not_logged_in(self):
        templates_url_names = (
            ('posts/index.html', reverse('posts:posts_index')),
            (
                'posts/group_list.html', reverse(
                    'posts:group_list', kwargs={'slug': self.post.group.slug}
                )
            ),
            (
                'posts/profile.html',
                reverse('posts:profile', kwargs={'username': self.post.author})
            ),
            (
                'posts/post_detail.html',
                reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
            ),
        )
        for template, address in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(HTTPStatus.OK, response.status_code)
                self.assertTemplateUsed(response, template)

    def test_unavailable_not_logged_in(self):
        urls = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(HTTPStatus.FOUND, response.status_code)

    def test_available_logged_in(self):
        templates_url_names = (
            ('posts/index.html', reverse('posts:posts_index')),
            (
                'posts/group_list.html', reverse(
                    'posts:group_list', kwargs={'slug': self.post.group.slug}
                )
            ),
            (
                'posts/profile.html', reverse(
                    'posts:profile', kwargs={'username': self.post.author}
                )
            ),
            (
                'posts/post_detail.html', reverse(
                    'posts:post_detail', kwargs={'post_id': self.post.pk}
                )
            ),
            ('posts/create_post.html', reverse('posts:post_create'))
        )
        for template, address in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(HTTPStatus.OK, response.status_code)
                self.assertTemplateUsed(response, template)

    def test_edit_only_author(self):

        client_and_response_code = (
            (
                self.authorized_client.get(
                    reverse(
                        'posts:post_edit', kwargs={'post_id': self.post.pk}
                    )
                ), HTTPStatus.FOUND
            ),
            (
                self.guest_client.get(
                    reverse(
                        'posts:post_edit', kwargs={'post_id': self.post.pk}
                    )
                ), HTTPStatus.FOUND
            ),
            (self.my_author.get(
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
            ), HTTPStatus.OK
            ),
        )
        for response, my_status in client_and_response_code:
            self.assertEqual(my_status, response.status_code)

    def test_unexisting_page(self):
        """Проверяем, что несуществующая страница вернет ошибку 404."""
        client_and_response_code = (
            (
                self.authorized_client.get('/unexisting_page/'),
                HTTPStatus.NOT_FOUND
            ),
            (self.guest_client.get('/unexisting_page/'), HTTPStatus.NOT_FOUND),
            (self.my_author.get('/unexisting_page/'), HTTPStatus.NOT_FOUND),
        )
        for response, response_code in client_and_response_code:
            with self.subTest(response_code=response_code):
                self.assertEqual(response_code, response.status_code)
                self.assertTemplateUsed(response, 'core/404.html')
