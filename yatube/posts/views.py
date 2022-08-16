from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница."""
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Обработка страниц сообществ отфильтрованных по группам."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Обработка профайла пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.all().filter(author__username=username)
    posts_qty = len(post_list)
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    following = False
    user = request.user
    if user.is_authenticated:
        if request.user.follower.filter(author=author).exists():
            following = True

    context = {
        'author': author,
        'posts_qty': posts_qty,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Обработка страницы отдельного поста."""
    post = get_object_or_404(Post, pk=post_id)
    posts_qty = Post.objects.filter(author_id=post.author.id).count()
    form = CommentForm()
    comments = Comment.objects.filter(post_id=post_id)
    context = {
        'post': post,
        'posts_qty': posts_qty,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание новой записи."""
    form = PostForm()

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(
                'posts:profile',
                username=request.user.get_username()
            )

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if request.user != post.author:
        return redirect(
            'posts:post_detail',
            post_id=post_id
        )

    if form.is_valid():
        post.save()
        return redirect(
            'posts:post_detail',
            post_id=post_id
        )

    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'post': post, 'is_edit': True}
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментариев к поссту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Вывод ленты постов автора, на которого
    подписан текущий пользователь."""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на интересующего автора."""
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:follow_index')

    Follow.objects.get_or_create(
        user=request.user,
        author=author
    )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписка от неинтересующего автора."""
    follow = (
        Follow.objects.filter(
            user=request.user
        ).filter(
            author__username=username
        )
    )
    follow.delete()
    return redirect('posts:follow_index')
