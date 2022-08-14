import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.user_no_name = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_no_name)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.post_with_group = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с указанием группы',
            group=cls.group,
        )
        cls.new_group = Group.objects.create(
            title='Пустая группа',
            slug='empty-group',
            description='Тестовое описание пустой группы',
        )
        cls.image_png = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.png',
            content=cls.image_png,
            content_type='image/png'
        )
        cls.post_with_image = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с картинкой',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post_with_image,
            author=cls.user_no_name,
            text='Тестовый комментарий'
        )
        cls.post_check_cache = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки кэширования',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_no_name,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user_not_author = User.objects.create_user(username='NotAuthor')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user_not_author)

# view-классы используют ожидаемые HTML-шаблоны

    def test_pages_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон"""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

# в шаблон передан правильный контекст и кэширование главной страницы

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.all().count()
        )
        self.assertContains(response, PostsPagesTests.post.text)
        self.assertContains(response, PostsPagesTests.post_with_group.text)
        self.assertContains(response, PostsPagesTests.post_with_image.text)
        for post in response.context['page_obj'].object_list:
            if post is PostsPagesTests.post_with_image:
                self.assertEqual(
                    post.image,
                    PostsPagesTests.post_with_image.image
                )

    def test_index_page_cache(self):
        """Проверка кэширования главной страницы."""
        response = self.guest_client.get(reverse('posts:index'))
        post_text = response.content

        PostsPagesTests.post_check_cache.delete()
        response = self.guest_client.get(reverse('posts:index'))
        post_cache = response.content

        self.assertEqual(
            post_text,
            post_cache,
        )

        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        post_cache_clear = response.content
        self.assertNotEqual(
            post_cache,
            post_cache_clear,
        )

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(
            len(response.context['page_obj']),
            PostsPagesTests.group.posts.all().count()
        )
        for post in response.context['page_obj'].object_list:
            if post is PostsPagesTests.post_with_image:
                self.assertEqual(
                    post.group.title,
                    PostsPagesTests.post_with_image.group.title
                )
                self.assertEqual(
                    post.group.slug,
                    PostsPagesTests.post_with_image.group.slug
                )
                self.assertEqual(
                    post.group.description,
                    PostsPagesTests.post_with_image.group.description
                )
                self.assertEqual(
                    post.author.username,
                    PostsPagesTests.post_with_image.author.username
                )
                self.assertEqual(
                    post.text,
                    PostsPagesTests.post_with_image.text
                )
                self.assertEqual(
                    post.image,
                    PostsPagesTests.post_with_image.image
                )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.user.username}
            )
        )
        self.assertEqual(
            response.context['author'].username,
            PostsPagesTests.user.username
        )
        self.assertEqual(
            response.context['posts_qty'],
            Post.objects.filter(
                author__username=PostsPagesTests.user.username
            ).count()
        )
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.filter(
                author__username=PostsPagesTests.user.username
            ).count()
        )
        for post in response.context['page_obj'].object_list:
            if post is PostsPagesTests.post_with_image:
                self.assertEqual(
                    post.image,
                    PostsPagesTests.post_with_image.image
                )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostsPagesTests.post_with_image.id}'}
            )
        )
        self.assertEqual(
            response.context['post'].id,
            PostsPagesTests.post_with_image.id
        )
        self.assertEqual(
            response.context['posts_qty'],
            Post.objects.filter(
                author_id=PostsPagesTests.post_with_image.author.id
            ).count()
        )
        self.assertEqual(
            response.context['post'].image,
            PostsPagesTests.post_with_image.image
        )
        self.assertEqual(
            response.context['comments'][0],
            PostsPagesTests.comment
        )
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = (
                    response.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = (
                    response.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        self.assertEqual(response.context['post'].id, self.post.id)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = (
                    response.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field, expected)

    def test_follow_index_show_correct_context(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.filter(author=PostsPagesTests.user).count()
        )

# дополнительные проверки

    def test_new_post_with_group_checking(self):
        """При создании поста с группой, пост отображается
        на главной странице, на странице группы, в профайле
        пользователя."""
        reverse_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertContains(response, self.post_with_group.text)

    def test_post_with_group_not_in_new_group(self):
        """Post_with_group не попал в группу, для которой
        не был предназначен."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'empty-group'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_follow_unfollow_available_for_authorized_user(self):
        """Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок."""
        follow_count = Follow.objects.count()
        response_1 = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_not_author.username},
            )
        )
        self.assertRedirects(
            response_1,
            reverse('posts:follow_index')
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=PostsPagesTests.user_no_name,
                author=self.user_not_author
            ).exists()
        )

        response_2 = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_not_author.username},
            )
        )
        self.assertRedirects(
            response_2,
            reverse('posts:follow_index')
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_new_post_in_followers_follow_index(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        new_post = Post.objects.create(
            author=PostsPagesTests.user,
            text='Тестовый пост для проверки подписок'
        )
        response_1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response_1, new_post.text)

        response_2 = self.not_author_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response_2, new_post.text)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        posts_numbers = 13
        for num in range(posts_numbers):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {num}',
                group=cls.group,
            )
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)

    def setUp(self):
        self.guest_client = Client()

        cache.clear()

    def test_first_pages_contains_ten_records(self):
        """Количество постов на первых страницах index,
        group_list, profile равно 10."""
        reverse_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        )

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_pages_contains_three_records(self):
        """Количество постов на вторых страницах index,
        group_list, profile равно 3."""
        reverse_names = (
            (reverse('posts:index') + '?page=2'),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': 'test-slug'}
                ) + '?page=2'
            ),
            (reverse('posts:profile', kwargs={'username': 'auth'}) + '?page=2')
        )

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 3)
