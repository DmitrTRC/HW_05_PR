from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        'date published', auto_now_add=True, db_index=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='author_posts')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              blank=True, null=True, related_name='group_posts')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text

    def get_pub_date(self):
        return self.pub_date.strftime('%d %b %Y')

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(
        'date published', auto_now_add=True, db_index=True)

    def __str__(self):
        return 'Comment {} by {}'.format(self.text, self.author.get_full_name())


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ['user', 'author']
        ordering = ('-created',)

    def __str__(self):
        return f'{self.user} follows {self.author}'


User.add_to_class('tracking', models.ManyToManyField('self', through=Follow,
                                                     related_name='followers', symmetrical=False))
