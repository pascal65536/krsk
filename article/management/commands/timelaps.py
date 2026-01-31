from django.core.management import BaseCommand
from django.utils import timezone
from article.models import Post
import pytz
import datetime


# python manage.py timelaps
class Command(BaseCommand):
    def handle(self, *args, **options):
        print("s" * 80)
        tz = pytz.timezone("Asia/Krasnoyarsk")
        tzinfo = datetime.timezone.utc
        post_qs = Post.objects.filter(deleted__isnull=False)
        for post_obj in post_qs:
            pod = post_obj.date_post
            pd = list()
            pd.append(datetime.datetime.now().year + 1)
            pd.append(pod.month)
            pd.append(pod.day)
            pd.append(pod.hour)
            pd.append(pod.minute)
            pd.append(pod.second)
            post_obj.date_post = datetime.datetime(*pd, tzinfo=tzinfo)
            post_obj.save()
            
