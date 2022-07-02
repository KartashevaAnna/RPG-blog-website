from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

User = get_user_model()


class StaticPagesURLTests(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create(username='OurTestUser')
        self.authorized_client.force_login(self.user)

    def test_urls_status_code(self):
        def verify_status_codes(my_client):
            my_urls = (reverse('about:tech'), reverse('about:author'))
            for my_url in my_urls:
                with self.subTest(url=my_url):
                    response = my_client.get(my_url, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

        my_clients = (self.guest_client, self.authorized_client)
        for my_client in my_clients:
            verify_status_codes(my_client)

    def test_namespace_correct(self):
        urls_and_templates = (
            ('about:tech', 'about/tech.html'),
            ('about:author', 'about/about.html')
        )
        for url, template in urls_and_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url), follow=True
                )
            self.assertTemplateUsed(response, template)
