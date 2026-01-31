from django.core.management import BaseCommand
from django.utils import timezone
from article.models import Post
import pytz
from datetime import datetime, timedelta


# python manage.py half
class Command(BaseCommand):
    def handle(self, *args, **options):
        print("s" * 80)

        krsk_tz = pytz.timezone("Asia/Krasnoyarsk")
        
        now_naive = datetime.now()
        tomorrow_naive = (now_naive + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_midnight_local = krsk_tz.localize(tomorrow_naive)
        tomorrow_midnight = tomorrow_midnight_local.astimezone(timezone.UTC)
        post_qs = Post.objects.filter(date_post__gt=tomorrow_midnight, deleted__isnull=True).order_by('date_post')

        for num, post_obj in enumerate(post_qs):
            pod = tomorrow_midnight + timedelta(hours=12 * num)
            post_obj.date_post = pod
            post_obj.save()
            
