from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from http import HTTPStatus
from django.core.cache import cache

from posts.models import Post, Group, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.test_user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='slug_for_test',
            description='Описание для теста',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.responses = (
            (
                'posts:posts',
                None,
                '/'
            ), (
                'posts:group_list',
                (cls.group.slug,),
                f'/group/{cls.group.slug}/'
            ), (
                'posts:profile',
                (cls.user.username,),
                f'/profile/{cls.user.username}/'
            ), (
                'posts:post_detail',
                (cls.post.pk,),
                f'/posts/{cls.post.pk}/'
            ), (
                'posts:post_create',
                None,
                '/create/'
            ), (
                'posts:post_edit',
                (cls.post.pk,),
                f'/posts/{cls.post.pk}/edit/'
            )
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)
        self.author = Client()
        self.author.force_login(self.user)
        cache.clear()

    def test_pages_for_all(self):
        """Страницы доступны всем пользователям"""
        names = ('posts:post_create', 'posts:post_edit')
        for name, arg, _ in self.responses:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=arg))
                if name in names:
                    expected = (
                        reverse(settings.LOGIN_URL)
                        + '?next='
                        + reverse(name, args=arg)
                    )
                    self.assertRedirects(response, expected)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_for_authorized_client(self):
        """Страницы доступны авторизованному пользователю"""
        for name, arg, _ in self.responses:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=arg))
                if name == 'posts:post_edit':
                    self.assertRedirects(
                        response,
                        reverse(
                            'posts:post_detail',
                            args=[self.post.pk]
                        )
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK
                    )

    def test_pages_for_author_1(self):
        """Страницы доступны автору"""
        for name, arg, _ in self.responses:
            with self.subTest(name=name):
                response = self.author.get(reverse(name, args=arg))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        """Тесты несуществующей страницы"""
        response = self.client.get('/unexisting/')
        self.assertTemplateUsed(response, 'core/404.html')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_reverse(self):
        for name, arg, adress in self.responses:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=arg), adress)

    def test_urls_and_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        test_data = (
            (
                'posts:posts',
                None,
                'posts/index.html'
            ), (
                'posts:group_list',
                (self.group.slug,),
                'posts/group_list.html'
            ), (
                'posts:profile',
                (self.user.username,),
                'posts/profile.html'
            ), (
                'posts:post_detail',
                (self.post.pk,),
                'posts/post_detail.html'
            ), (
                'posts:post_create',
                None,
                'posts/create_post.html'
            ), (
                'posts:post_edit',
                (self.post.pk,),
                'posts/create_post.html'
            ),
        )
        for name, arg, template in test_data:
            with self.subTest(name=name):
                address = reverse(name, args=arg)
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)
