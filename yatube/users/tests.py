from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class StaticPagesUrlTests(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = User.objects.create(username='MyUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_available_for_logged_in(self):
        my_dict = {
            '/auth/logout/': HTTPStatus.OK,
            '/auth/signup/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
        }
        for address, response_code in my_dict.items():
            with self.subTest(response_code=response_code):
                response = self.authorized_client.get(address)
                self.assertEqual(response_code, response.status_code)

    def test_available_for_logged_out(self):
        urls_vs_codes = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
        }
        for address, response_code in urls_vs_codes.items():
            with self.subTest(response_code=response_code):
                response = self.guest_client.get(address)
                self.assertEqual(response_code, response.status_code)

    def test_namespace_correct(self):
        '''Проверяем, что у нас корректно работают переопределенные ссылки.'''
        urls_and_templates = {
            'users:logout': 'users/logged_out.html',
            'users:signup': 'users/signup.html',
            'users:login': 'users/login.html',
            'users:password_reset': 'users/password_reset_form.html',
            'users:password_change': 'users/password_change_form.html',
            'users:password_change_done': 'users/password_change_done.html',
            'users:password_reset_confirm':
                'users/password_reset_confirm.html',
            'users:password_reset_complete':
                'users/password_reset_complete.html',
        }
        for url, template in urls_and_templates.items():
            with self.subTest(url=url):
                self.authorized_client.force_login(self.user)
                if url == 'users:password_reset_confirm':
                    self.password_reset_token = \
                        PasswordResetTokenGenerator().make_token(self.user)
                    self.password_reset_uid = force_str(
                        urlsafe_base64_encode(force_bytes(self.user.pk)))
                    response = self.authorized_client.get(
                        reverse(url, kwargs={'uidb64': 'password_reset_uid',
                                             'token': 'password_reset_token'}),
                        follow=True)
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.authorized_client.get(
                        reverse(url), follow=True)
                    self.assertTemplateUsed(response, template)

    def test_create_new_user(self):
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Kartasheva',
            'last_name': 'Anna',
            'username': 'MyTestUser',
            'email': 'annakartashevamail@gmail.com',
            'password1': '16dglsdgkasnk4',
            'password2': '16dglsdgkasnk4',
        }
        self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
