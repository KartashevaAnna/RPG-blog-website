import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAnna')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Вторая тестовая группа',
            slug='another_group',
            description='Еще одно описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        my_post = Post.objects.latest('created')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(my_post.text, form_data['text'])
        self.assertEqual(my_post.group.id, form_data['group'])
        self.assertEqual(my_post.image.name[6:], form_data['image'].name)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id,
        }
        new_form_data = {
            'text': 'Новый текст',
            'group': self.another_group.id,
        }
        self.verify_change(form_data, posts_count)
        self.verify_change(new_form_data, posts_count)

    def verify_change(self, form_data, posts_count):
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=1)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AnnaTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='My test text',
            author=cls.user,
            group=cls.group,
        )
        cls.first_comment = {
            'post': cls.post,
            'text': 'мой новый комментарий',
        }
        cls.another_comment = {
            'post': cls.post,
            'text': 'совсем другой текст',
        }

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def get_post_detail(self, client):
        post_detail_page = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        return post_detail_page

    def adding_comment(self, my_client, my_comment):
        added = my_client.post(reverse(
            'posts:add_comment', kwargs={
                'post_id': self.post.id,
            }
        ), data=my_comment, follow=False
        )
        return added

    def test_add_comment_by_authorized_user(self):
        comments_count = self.post.comments.all().count()
        adding = self.adding_comment(self.authorized_client,
                                     self.first_comment)
        my_page = self.get_post_detail(self.authorized_client)
        expected = self.post.comments.filter(
            text=self.first_comment['text']).exists()
        my_comment = Comment.objects.latest('-created')
        new_comments_count = self.post.comments.all().count()
        with self.subTest(new_comment=self.first_comment):
            self.assertEqual(adding.status_code, HTTPStatus.FOUND)
            self.assertEqual(
                comments_count + 1, new_comments_count
            )
            self.assertTrue(expected, 'Comment is added')
            self.assertEqual(self.first_comment['text'], my_comment.text)
            self.assertEqual(my_comment.pk, new_comments_count)
            self.assertIn(my_comment, my_page.context['comments'])

    def test_no_comment_by_guest_client(self):
        comments_count = self.post.comments.all().count()
        adding = self.adding_comment(self.guest_client, self.another_comment)
        self.get_post_detail(self.guest_client)
        expected = self.post.comments.filter(
            text=self.another_comment['text']).exists()
        new_comments_count = self.post.comments.all().count()
        with self.subTest(another_comment=self.another_comment):
            self.assertFalse(expected, 'Comment is added when it shan\'t')
            self.assertEqual(comments_count, new_comments_count)
            self.assertEqual(adding.status_code, HTTPStatus.FOUND)
