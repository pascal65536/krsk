from django.core.management.base import BaseCommand
from article.models import Post
from tag.models import Tag
from django.utils import timezone


class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle_12(self, *args, **options):
        for post in Post.objects.all():
            post.tag.clear()
        Tag.objects.all().delete()
        return '2' * 20

    def handle(self, *args, **options):
        for post in Post.objects.filter(deleted__isnull=True, date_post__lte=timezone.now()):
            print(post)
            post.update_tags()

        return '2' * 20


