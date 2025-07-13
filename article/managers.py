from django.db import models
from django.utils import timezone
from datetime import timedelta


class PostManager(models.Manager):
    """
    Менеджер постов
    """
    def for_user(self, user=None):
        if user and user.is_superuser:
            qs = self.filter(date_post__lte=(timezone.now() + timedelta(weeks=1)))
        else:
            qs = self.filter(deleted__isnull=True, date_post__lte=timezone.now())
        qs = qs.order_by("-date_post")
        return qs
