import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.test_user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='slug_for_test',
            description='Описание для теста'
        )
        cls.new_group = Group.objects.create(
            title='Новая группа для теста',
            slug='new_slug_for_test',
            description='Описание для теста'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)
        self.author = Client()
        self.author.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает пост."""
        Post.objects.all().delete()
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
        test_data = {
            'text': 'this is text',
            'group': self.group.pk,
            'image': uploaded
        }
        self.authorized_client.post(reverse('posts:post_create'), test_data)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(
            post.author,
            self.test_user,
            'Неверно показан автор'
        )
        self.assertEqual(
            post.group.pk,
            test_data['group'],
            'Неверно показанa группа'
        )
        self.assertEqual(
            post.text,
            test_data['text'],
            'Неверно показан текст'
        )
        self.assertTrue(
            Post.objects.filter(
                text='this is text',
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует пост."""
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 1, 'Неверное количество постов')
        form_data = {
            'text': 'new_text',
            'group': self.new_group.pk,
        }
        self.author.post(reverse('posts:post_edit', args=[
            self.post.pk
        ]), form_data)
        post = Post.objects.first()
        self.assertEqual(
            post.author,
            self.post.author,
            'Неверно показан автор'
        )
        self.assertEqual(
            post.group.pk,
            form_data['group'],
            'Неверно показан группа'
        )
        self.assertEqual(
            post.text,
            form_data['text'],
            'Неверно показан текст'
        )
        response_old_group = self.author.get(reverse(
            'posts:group_list',
            args=[self.group.slug]
        ))
        self.assertEqual(response_old_group.status_code, HTTPStatus.OK)
        self.assertEqual(len(response_old_group.context['page_obj']), 0)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_client_cant_create_posts(self):
        posts_count_1 = Post.objects.count()
        form_data = {
            'text': 'this is text',
            'group': self.group.pk
        }
        self.client.post(reverse('posts:post_create'), form_data)
        posts_count_2 = Post.objects.count()
        self.assertEqual(posts_count_1, posts_count_2)

    def test_access_to_comments(self):
        """Доступ к комментариям и контекст"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий о том, что я ненавижу тесты'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                args=[self.post.pk]
            ), data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий о том, что я ненавижу тесты',
            ).exists()
        )
        comment = Comment.objects.get(pk=1)
        self.assertEqual(comment.author, self.test_user)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        response_authorized = self.authorized_client.get(reverse(
            'posts:post_detail',
            args=[self.post.pk]
        ))
        self.assertTrue(
            response_authorized.context['comments'],
            form_data['text']
        )

    def test_client_has_no_access_to_comments(self):
        """Анонимный пользователь не может комментировать посты"""
        count_before = Comment.objects.count()
        form_data = {
            'text': 'Комментарий о том, что я ненавижу тесты'
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                args=[self.post.pk]
            ), data=form_data
        )
        count_after = Comment.objects.count()
        self.assertEqual(count_before, count_after)
