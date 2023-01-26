from django.conf import settings
from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост хоть бы тут было больше пятнадцати символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group_fail = 'Неверно работает __str__ у модели группы'
        post_fail = 'Неверно работает __str__ у модели поста'
        self.assertEqual(
            self.post.__str__(),
            self.post.text[:settings.NUMBER_OF_SYMBOLS],
            post_fail
        )
        self.assertEqual(
            self.group.__str__(),
            self.group.title,
            group_fail
        )

    def test_verbose_name(self):
        verbose_names = (
            (
                self.post._meta.get_field('text').verbose_name,
                'текст'
            ), (
                self.post._meta.get_field('pub_date').verbose_name,
                'дата публикации'
            ), (
                self.post._meta.get_field('author').verbose_name,
                'автор'
            ), (
                self.post._meta.get_field('group').verbose_name,
                'группа'
            )
        )
        for meta, name in verbose_names:
            with self.subTest(name=name):
                self.assertEqual(meta, name)

    def test_help_text(self):
        help_texts = (
            (
                self.post._meta.get_field('text').help_text,
                'Введите текст поста'
            ), (
                self.post._meta.get_field('group').help_text,
                'Выберите группу из предложенных'
            )
        )
        for meta, help_text in help_texts:
            with self.subTest(help_text=help_text):
                self.assertEqual(meta, help_text)
