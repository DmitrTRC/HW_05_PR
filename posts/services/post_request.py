from posts.models import Post, Group, User, Comment
from django.shortcuts import get_object_or_404, redirect
import datetime as dt
from django.core.paginator import Paginator


def get_latest_posts(request, limit=10):
    post_list = Post.objects.order_by("-pub_date").all()
    # показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10)

    # переменная в URL с номером запрошенной страницы
    page_number = request.GET.get('page')
    # получить записи с нужным смещением
    page = paginator.get_page(page_number)
    return {'page': page, 'paginator': paginator}


def get_page_setup(request, slug):
    # Return 404 error if not found
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return {'group': group, 'paginator': paginator, 'page': page}


def search_keyword(request):
    keyword = request.GET.get("q", None)
    if keyword:
        posts = Post.objects.select_related(
            'author', 'group').filter(text__contains=keyword)
    else:
        posts = None

    return {'posts': posts, 'keyword': keyword}


def get_user_subscribers(r_user):
    pass


def get_user_info(request, username):
    user = get_object_or_404(User, username__exact=username)
    post_list = user.author_posts.all().order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    # переменная в URL с номером запрошенной страницы
    page_number = request.GET.get('page')
    # получить записи с нужным смещением
    page = paginator.get_page(page_number)
    print('Tracking : ', user.tracking.count())
    print('Followers :', user.followers.count())
    return {'profile': user, 'paginator': paginator, 'page': page}


def get_single_page(username, post_id):
    user = get_object_or_404(User, username__exact=username)
    post = get_object_or_404(Post, pk=post_id)
    return {'post_view': user, 'post': post}
