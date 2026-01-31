from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz
from datetime import datetime, timedelta
from article.models import Post

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("s" * 80)
        
        # Часовой пояс Красноярска
        krsk_tz = pytz.timezone("Asia/Krasnoyarsk")
        
        # Полночь следующего дня (naive)
        now_naive = datetime.now()
        tomorrow_naive = (now_naive + timedelta(days=2)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Локализуем в Красноярске
        tomorrow_midnight_local = krsk_tz.localize(tomorrow_naive)
        
        # Конвертируем в UTC с pytz.UTC (работает в старых Django)
        tomorrow_midnight = tomorrow_midnight_local.astimezone(pytz.UTC)
        
        # Фильтр по будущим статьям
        post_qs = Post.objects.filter(
            date_post__gte=tomorrow_midnight,
            deleted__isnull=True
        ).order_by('date_post')
        
        for num, post_obj in enumerate(post_qs):
            publish_time = tomorrow_midnight + timedelta(hours=9 * num)
            
            # print(f"Статья: {post_obj.title}")
            # print(f"Было: {post_obj.date_post}")
            # print(f"Станет: {publish_time}")
            # print("-" * 50)
            
            # Раскомментируйте для сохранения:
            post_obj.date_post = publish_time
            post_obj.save()
