import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.conf import settings
from posts.forms import PostForm
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.test_user = User.objects.create_user(username='StasBasov')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='slug_for_test',
            description='Описание для теста'
        )
        cls.group2 = Group.objects.create(
            title='Группа для теста',
            slug='slug_for_test2',
            description='Описание для теста'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.image
        )
        cls.response_index = reverse('posts:posts')
        cls.response_group_list = reverse('posts:group_list', args=[
            cls.group.slug
        ])
        cls.response_profile = reverse('posts:profile', args=[
            cls.user.username
        ])
        cls.response_post_detail = reverse('posts:post_detail', args=[
            cls.post.pk
        ])
        cls.response_post_create = reverse('posts:post_create')
        cls.response_post_edit = reverse('posts:post_edit', args=[
            cls.post.pk
        ])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.test_user)
        self.author = Client()
        self.author.force_login(StaticURLTests.user)
        cache.clear()

    def additional_function(self, request, boolean=False):
        """Вспомогательная функция"""
        if boolean is True:
            post = request.context['post']
        else:
            post = request.context.get('page_obj')[0]
        for_test = {
            post.text: self.post.text,
            post.pub_date: self.post.pub_date,
            post.author: self.post.author,
            post.group: self.post.group,
            post.image: self.post.image,
        }
        for expected, real in for_test.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        self.additional_function(
            self.authorized_client.get(self.response_index)
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response_group_list = self.authorized_client.get(
            self.response_group_list
        )
        self.additional_function(response_group_list)
        group_name = self.group
        test_group_title_context = response_group_list.context['group']
        message = 'Неверно отображается название группы'
        self.assertEqual(
            group_name,
            test_group_title_context,
            message
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response_profile = self.authorized_client.get(
            self.response_profile
        )
        self.additional_function(response_profile)
        author = self.user
        test_author_context = response_profile.context['author']
        message = 'Неверно отображается автор'
        self.assertEqual(
            author,
            test_author_context,
            message
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        self.additional_function(
            self.authorized_client.get(self.response_post_detail),
            boolean=True
        )

    def test_posts_not_in_the_another_group(self):
        self.group3 = Group.objects.create(
            title='Группа для теста',
            slug='slug_for_test3',
            description='Описание для теста'
        )
        response_group_3 = self.author.get(reverse(
            'posts:group_list',
            args=[self.group3.slug]
        ))
        self.assertEqual(len(response_group_3.context.get('page_obj')), 0)
        post = Post.objects.first()
        self.assertEqual(post.group, self.post.group)

    def test_post_edit_and_post_create_pages_show_correct_context(self):
        """Шаблон post_edit и post_create с правильным контекстом."""
        test_data = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.pk,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for name, argument in test_data:
            with self.subTest(name=name):
                response = self.author.get(reverse(name, args=argument))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form'
                        ).fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_index_page_contains_ten_and_three_records(self):
        Follow.objects.create(user=self.test_user, author=self.user)
        Post.objects.filter(id=1).delete()
        bulk_list = []
        number_of_posts = 13
        for post in range(number_of_posts):
            bulk_list.append(Post(
                text=f'Какой-то текст {post}',
                author=self.user,
                group=self.group,
            ))
        Post.objects.bulk_create(bulk_list)
        adresses = (
            ('posts:posts', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:follow_index', None)
        )
        pages_and_number_of_posts = (
            ('?page=1', settings.NUMBER_OF_POSTS),
            ('?page=2', number_of_posts - settings.NUMBER_OF_POSTS)
        )
        for adress, argument in adresses:
            with self.subTest(adress=adress):
                for page, number in pages_and_number_of_posts:
                    with self.subTest(page=page):
                        response = self.authorized_client.get(
                            reverse(adress, args=argument)
                            + page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']),
                            number
                        )

    def test_cache(self):
        """Проверка кеша"""
        response = self.authorized_client.get(reverse('posts:posts'))
        Post.objects.filter(pk=1).delete()
        post_first = response.content
        response_2 = self.authorized_client.get(reverse('posts:posts'))
        post_second = response_2.content
        self.assertEqual(post_first, post_second)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:posts'))
        post_cleared = response_3.content
        self.assertNotEqual(post_second, post_cleared)

    def test_follow(self):
        """Авторизованный пользователь может подписываться"""
        count_before_follow = Follow.objects.all().count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user.username]
        )
        )
        count_after = Follow.objects.all().count()
        self.assertEqual(
            count_before_follow + 1,
            count_after,
            'Не подписался'
        )
        follow_data = Follow.objects.get(pk=1)
        self.assertEqual(follow_data.author, self.user)
        self.assertEqual(follow_data.user, self.test_user)

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться"""
        Follow.objects.create(user=self.test_user, author=self.user)
        count_before = Follow.objects.all().count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            args=[self.user.username]
        )
        )
        count_after_unfollow = Follow.objects.all().count()
        self.assertEqual(
            count_before - 1,
            count_after_unfollow,
            'Не отписался'
        )

    def test_new_index_follow(self):
        """Новая запись в ленте подписчиков"""
        response_1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response_1.context.get('page_obj')),
            0,
            'Не получилось'
        )
        Follow.objects.create(user=self.test_user, author=self.user)
        response_2 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response_2.context.get('page_obj')),
            1,
            'Не получилось'
        )

    def test_follow_myself(self):
        """При подписке на себя количество подписок не меняется"""
        count_before = Follow.objects.all().count()
        self.author.get(reverse(
            'posts:profile_unfollow',
            args=[self.user.username]
        )
        )
        count_after = Follow.objects.all().count()
        self.assertEqual(count_before, count_after)

    def test_follow_2_times(self):
        """тест повторной подписки - кол-во равно 1"""
        count_before = Follow.objects.all().count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user.username]
        )
        )
        count_after = Follow.objects.all().count()
        self.assertEqual(count_before + 1, count_after)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user.username]
        )
        )
        count_after_2_follow = Follow.objects.all().count()
        self.assertEqual(count_after, count_after_2_follow)
