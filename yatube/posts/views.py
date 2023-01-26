from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow, Comment
from .utils import page_counter


@cache_page(20 * 1)
def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    context = {
        'page_obj': page_counter(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    context = {
        'group': group,
        'page_obj': page_counter(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user).exists()
                 )
    post_list = author.posts.select_related('group').all()
    context = {
        'author': author,
        'page_obj': page_counter(request, post_list),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.all().filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).all()
    context = {
        'page_obj': page_counter(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    if request.user.username != username:
        follow, created = Follow.objects.get_or_create(
            user=request.user,
            author=following
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(Follow, user=request.user, author=following)
    follower.delete()
    return redirect('posts:profile', username=username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
