from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_models_have_correct_verbose_name(self):
        """Проверяем, что у полей корректно работает человекочитаемое имя."""
        post = self.post
        verbose_group = post._meta.get_field('group').verbose_name
        verbose_author = post._meta.get_field('author').verbose_name
        verbose_and_expected = (
            (verbose_group, 'Группа'),
            (verbose_author, 'Автор'),
        )
        for value, expected in verbose_and_expected:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_models_have_correct_help_text(self):
        """Проверяем, что у полей корректно работают подсказки."""
        post = self.post
        help_text_group = post._meta.get_field('group').help_text
        self.assertEqual(
            'Группа, к которой будет относиться пост',
            help_text_group
        )

    def test_str_correct(self):
        my_objects_and_expected = (
            (str(self.group), self.group.title),
            (str(self.post), self.post.text[:15])
        )
        for value, expected in my_objects_and_expected:
            with self.subTest(value=value):
                self.assertEqual(value, expected)
