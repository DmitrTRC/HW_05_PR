from django.test import TestCase, Client
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from posts.models import Post, Group
from django.urls import reverse, reverse_lazy
from django.core.cache import cache
import time
from posts.forms import CommentForm

User = get_user_model()


class PostEditTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.staff_user = User.objects.create_superuser(username='dmitry', password='developer',
                                                        email='morozovd@me.com')
        self.non_author_user = User.objects.create_user(username='kolya', password='developer',
                                                        email='kolya@blanes.com')
        self.anonymous_user = AnonymousUser()

        Post.objects.create(pk=1, author=self.staff_user,
                            text='TEST DATA PATTERN')
        cache.clear()

    def test_check_up(self):
        self.assertEqual(self.staff_user.author_posts.all().count(), 1)

    def test_user_page_created(self):
        url = reverse_lazy('profile', kwargs={
                           'username': self.staff_user.username})
        status = self.client.get(url).status_code
        self.assertEqual(status, 200, msg=status)
        self.client.force_login(self.staff_user)
        url = reverse_lazy('post_edit', kwargs={'username': self.staff_user.username,
                                                'post_id': 1})
        status = self.client.get(url).status_code
        self.assertEqual(status, 200, msg=(status, url))

    def test_restricted_user_redirect(self):
        url = reverse_lazy('post_edit', kwargs={'username': self.non_author_user.username,
                                                'post_id': 1})
        status = self.client.get(url).status_code
        self.assertEqual(status, 302, msg='Wrong 1')
        self.client.force_login(self.non_author_user)
        status = self.client.get(url).status_code
        self.assertEqual(status, 404, msg='Wrong 2')
        self.client.logout()
        url = reverse_lazy('post_edit', kwargs={'username': self.staff_user.username,
                                                'post_id': 1})
        self.client.force_login(self.staff_user)
        status = self.client.get(url).status_code
        self.assertEqual(status, 200, msg=('Wrong 3', status))

    def test_permissions(self):
        self.assertEqual(self.non_author_user.has_perm(
            'auth.change_user'), False)
        self.client.force_login(self.non_author_user)
        self.client.logout()
        self.assertEqual(self.non_author_user.is_authenticated, True)

    def test_new_post_permissions(self):
        response = self.client.get(reverse_lazy('new_post'))
        self.assertRedirects(response, '/auth/login/?next=/new/', status_code=302, target_status_code=200,
                             msg_prefix='',
                             fetch_redirect_response=True)

    def test_new_post_create(self):
        url = reverse_lazy('new_post')
        status = self.client.get(url).status_code
        self.assertEqual(status, 302 or 301, msg=('Not redirected', status))
        self.client.force_login(self.non_author_user)
        status = self.client.get(url).status_code
        self.assertEqual(status, 200, msg=('Not granted', status))

    def test_new_post_content(self):
        tst_msg = 'Special test message tag=morozovd@me.com'
        self.client.force_login(self.non_author_user)
        url = reverse_lazy('new_post')
        self.client.post(url, {
            'author': self.non_author_user,
            'text': tst_msg,
        })
        post_id = Post.objects.get(text__exact=tst_msg).id
        url = reverse_lazy('index')
        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        url = reverse_lazy('profile', kwargs={
                           'username': self.non_author_user.username})
        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        url = reverse_lazy('post', kwargs={'username': self.non_author_user.username,
                                           'post_id': post_id})

        response = self.client.get(url)
        self.assertContains(response, tst_msg)

    def test_edit_post_content(self):
        tst_msg = 'Special test message tag=morozovd@me.com'
        new_msg = 'New message test 9984398@gmail.com'

        self.client.force_login(self.non_author_user)
        url = reverse_lazy('new_post')
        self.client.post(url, {
            'author': self.non_author_user,
            'text': tst_msg,
        })
        url = reverse_lazy('index')
        response = self.client.get(url)
        self.assertContains(response, tst_msg)

        post_id = Post.objects.get(text__exact=tst_msg).id

        url = reverse_lazy('post_edit', kwargs={
            'username': self.non_author_user.username,
            'post_id': post_id,
        })

        status = self.client.post(url, {
            'text': new_msg,
        }
        ).status_code
        self.assertEqual(status, 302 or 301, msg=('Not granted', status))

        url = reverse('index')

        # Remember to clear cache here!

        cache.clear()
        response = self.client.get(url)
        self.assertContains(response, new_msg)

        url = reverse_lazy('profile', kwargs={
                           'username': self.non_author_user.username})
        response = self.client.get(url)
        self.assertContains(response, new_msg)

        url = reverse_lazy('post', kwargs={'username': self.non_author_user.username,
                                           'post_id': post_id})
        response = self.client.get(url)
        self.assertContains(response, new_msg)

    def test_get_404_error(self):
        code = self.client.get(reverse_lazy('profile',
                                            kwargs={
                                                'username': self.staff_user.username
                                            }) + '/unreachable_page_404/').status_code
        self.assertEqual(code, 404, msg=(
            "Server doesn't returns 404 code!", code))

    def test_image_on_post(self):

        tst_msg = 'test graphics message tag=morozovd@me.com'
        img_msg = '<img class'
        group = Group(title='test', slug='test', description='test')
        group.save()
        self.client.force_login(self.non_author_user)
        url = reverse_lazy('new_post')
        with open('chair.jpeg', 'rb+') as fd:
            self.client.post(url, {
                'author': self.non_author_user,
                'text': tst_msg,
                'image': fd,
            })

        post = Post.objects.get(text=tst_msg)
        post.group = group
        post.save()
        url = reverse_lazy('group_posts', kwargs={'slug': 'test'})
        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        self.assertContains(response, img_msg)
        url = reverse_lazy('index')

        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        self.assertContains(response, img_msg)
        url = reverse_lazy('profile', kwargs={
                           'username': self.non_author_user.username})
        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        self.assertContains(response, img_msg)
        url = reverse_lazy('post', kwargs={'username': self.non_author_user.username,
                                           'post_id': post.id})

        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        self.assertContains(response, img_msg)

    def test_wrong_img_format(self):
        tst_msg = 'wrong graphics message tag=morozovd@me.com'
        img_msg = '<img class'
        self.client.force_login(self.non_author_user)
        url = reverse_lazy('new_post')
        with open('requirements.txt', 'rb+') as fd:
            self.client.post(url, {
                'author': self.non_author_user,
                'text': tst_msg,
                'image': fd,
            })
        url = reverse_lazy('index')
        response = self.client.get(url)
        self.assertNotContains(response, tst_msg)
        self.assertNotContains(response, img_msg)

    def test_cache_page(self):
        test_key = 'morozovd@me.com'
        cache.set('index_page', test_key, 1)
        result = cache.get('index_page')
        self.assertEqual(result, test_key)
        time.sleep(2)
        result = cache.get('index_page')
        self.assertNotEqual(result, test_key)

    def test_user_can_follow_unfollow(self):
        self.client.force_login(self.non_author_user)
        self.assertEqual(self.staff_user.followers.all().count(), 0)
        for _ in range(2):
            code = self.client.get(reverse_lazy('profile_follow', kwargs={
                'username': self.staff_user.username,
            })).status_code
            self.assertEqual(code, 302)
            self.assertEqual(self.staff_user.followers.all().count(), 1)
            # Perform test 2 times to be assure that only one follower added.
        # Unfollow section
        code = self.client.get(reverse_lazy('profile_unfollow', kwargs={
            'username': self.staff_user.username,
        })).status_code
        self.assertEqual(code, 302)
        self.assertEqual(self.staff_user.followers.all().count(), 0)

    def test_only_subscribed_news(self):
        tst_msg = 'Special test message tag=morozovd@me.com'
        unsubscribed_user = User.objects.create_user(username='vasya', password='developer',
                                                     email='vasya@blanes.com')
        self.client.force_login(self.non_author_user)
        code = self.client.get(reverse_lazy('profile_follow', kwargs={
            'username': self.staff_user.username,
        })).status_code
        self.assertEqual(code, 302)
        # We have subscribtion
        self.assertEqual(self.staff_user.followers.all().count(), 1)
        # We haven't subscibtion
        self.assertEqual(unsubscribed_user.followers.all().count(), 0)
        self.client.force_login(self.staff_user)
        url = reverse_lazy('new_post')
        self.client.post(url, {
            'author': self.staff_user,
            'text': tst_msg,
        })
        self.client.logout()
        self.client.force_login(self.non_author_user)
        response = self.client.get(reverse_lazy('follow_index'))
        self.assertContains(response, tst_msg)

        #  Then try out non-subscribed client

        self.client.logout()
        self.client.force_login(unsubscribed_user)
        response = self.client.get(reverse_lazy('follow_index'))
        self.assertNotContains(response, tst_msg)

    def test_post_comment_system_chcek(self):
        tst_msg = 'Special test message tag=morozovd@me.com'
        comment_msg = 'Special comment message tag=--xx--'

        self.client.force_login(self.staff_user)
        url = reverse_lazy('new_post')
        self.client.post(url, {
            'author': self.staff_user,
            'text': tst_msg,
        })
        post = Post.objects.get(text=tst_msg)
        self.client.logout()

        #  Test post is created

        url = reverse_lazy('post', kwargs={
            'username': self.staff_user.username,
            'post_id': post.id,
        })
        print(url)
        self.client.force_login(self.non_author_user)
        code = self.client.post(url, kwargs={
            'form.text': tst_msg,
        }).status_code
        response = self.client.get(url)
        self.assertContains(response, tst_msg)
        self.client.logout()

        # Now try Anonymous

        code = self.client.post(url, kwargs={
            'form.text': comment_msg,
        }).status_code
        response = self.client.get(url)
        self.assertNotContains(response, comment_msg)
