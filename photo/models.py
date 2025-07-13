import uuid
from django.db import models
from django.utils.safestring import mark_safe
from django.conf import settings


def get_file_path(instance, filename):
    ext = filename.split(".")[-1]
    uid = str(uuid.uuid4()) or "JPG"
    return f"{uid[:3]}/{uid[3:6]}/{uid}.{ext.lower()}"


class Photo(models.Model):
    title = models.CharField(verbose_name="Название", max_length=255)
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    picture = models.ImageField(verbose_name="Картинка", upload_to=get_file_path)

    image_size = models.IntegerField(verbose_name="Размер", default=0)
    content_type = models.CharField(verbose_name="Тип", max_length=255, blank=True, null=True)

    created = models.DateTimeField(verbose_name="Создано", auto_now_add=True)
    changed = models.DateTimeField(verbose_name="Изменено", auto_now=True)
    deleted = models.DateTimeField(verbose_name="Удалено", blank=True, null=True)

    def save(self, *args, **kwargs):
        self.image_size = self.picture.size
        self.content_type = self.picture.instance.content_type
        super().save(*args, **kwargs)


    @property
    def size(self):
        if self.image_size:
            return self.image_size
        return self.picture.size

    @property
    def url(self):
        return settings.PROTO_DOMAIN + self.picture.url

    def image_img(self):
        """
        Вывод картинок в админке
        """
        if not self.picture:
            return "(Нет изображения)"
        html = [
            f'<a href="{self.picture.url}" target="_blank">',
            f'<img src="{self.picture.url}" width="100"/></a>',
        ]
        return mark_safe(''.join(html))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фото"
        ordering = ["-created"]
