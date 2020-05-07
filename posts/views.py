from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .services import post_request
from .models import Post, Comment, Follow
from posts.models import User
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST


def index(request):
    return render(request, 'index.html', post_request.get_latest_posts(request, 10))


def group_posts(request, slug):
    print('request for group {}'.format(slug))
    return render(request, 'group.html', post_request.get_page_setup(request, slug))


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()

            return redirect('index')

    return render(request, 'post_new.html', {'form': form})


@require_POST
@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = request.user
    comments = post.comments.all()
    new_comment = None
    comment_form = CommentForm(request.POST)
    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.post = post
        new_comment.author = author
        new_comment.save()
        return redirect('post', username, post_id)


def profile(request, username):
    return render(request, 'profile.html', post_request.get_user_info(request, username))


def post_view(request, username, post_id):
    user = get_object_or_404(User, username__exact=username)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    comment_form = CommentForm()
    context = {
        'form': comment_form,
        'items': comments,
        'post_view': user,
        'post': post,
    }

    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    user_profile = get_object_or_404(User, username__exact=username)
    if user_profile != request.user:
        return redirect('post', username=request.user.username, post_id=post_id)
    post = get_object_or_404(Post, id__exact=post_id, author=user_profile)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username, post_id)

    content = {
        'form': form,
        'profile': user_profile,
        'post': post
    }

    return render(request, 'post_new.html', content)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)

# Following section


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__in=request.user.tracking.all()).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator, })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', author)
