from django.db import models
from krasnoarsk.utils import cyr2lat


class Tag(models.Model):
    title = models.CharField(max_length=50, unique=True, blank=False, null=False)

    @property
    def slug(self):
        return cyr2lat(self.title)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Название тега"
        verbose_name_plural = "Названия тегов"
        ordering = ["title"]
