import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.user_no_name = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_no_name)

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """При отправке валидной формы с картинкой со страницы
        создания поста, создается новая запись в базе данных."""
        posts_count = Post.objects.count()

        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test_gif.gif',
            content=test_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Новый текст',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostFormTests.user_no_name.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст',
                group=PostFormTests.group.id,
                image='posts/test_gif.gif'
            ).exists()
        )

    def test_post_edit(self):
        """При отправке валидной формы с картинкой со страницы
        редактирования поста, происходит изменение поста в базе данных."""
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test_image.gif',
            content=test_image,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст. Отредактировано',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse(
                'posts:post_edit',
                args=(f'{PostFormTests.post.id}',)
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostFormTests.post.id}'}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст. Отредактировано',
                group=PostFormTests.group.id,
                image='posts/test_image.gif'
            ).exists()
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.user_no_name = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_no_name)

        cls.form = CommentForm()

        def test_add_comment(self):
            """При отправке валидной формы с комментарием со страницы
            поста, комментарий появляется на странице поста."""
            form_data = {
                'text': 'Test comment',
            }
            response = self.authorizded_client.post(
                reverse(
                    'posts:add_comment',
                    args=(f'{CommentFormTests.post.id}',)
                ),
                data=form_data,
                follow=True
            )
            self.assertRedirects(
                response,
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': f'{CommentFormTests.post.id}'}
                )
            )
            self.assertTrue(
                Comment.objects.filter(
                    text='Test comment',
                    author=PostFormTests.user_no_name.username
                ).exists()
            )
