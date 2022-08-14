from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Follow, Group, Post

User = get_user_model()


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
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_labels(self):
        labels = {
            (
                PostModelTest.post._meta.get_field('text').verbose_name
            ): 'Текст поста',
            PostModelTest.post._meta.get_field('group').verbose_name: 'Группа',
            (
                PostModelTest.post._meta.get_field('image').verbose_name
            ): 'Картинка',
        }
        for verbose_name, label in labels.items():
            with self.subTest(verbose_name=verbose_name):
                self.assertEqual(verbose_name, label)

    def test_help_texts(self):
        help_texts = {
            (
                PostModelTest.post._meta.get_field('text').help_text
            ): 'Текст нового поста',
            (
                PostModelTest.post._meta.get_field('group').help_text
            ): 'Группа, к которой будет относиться пост',
            (
                PostModelTest.post._meta.get_field('image').help_text
            ): 'Загрузите сюда Ваше изображение',
        }
        for help_text, text in help_texts.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(help_text, text)


class GroupModelTest(TestCase):
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
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_follower = User.objects.create_user(username='user_follower')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Follow корректно работает __str__."""
        follow = FollowModelTest.follow
        user = FollowModelTest.follow.user.username
        author = FollowModelTest.follow.author.username
        expected_object_name = f'{user} подписан на {author}'
        self.assertEqual(expected_object_name, str(follow))
