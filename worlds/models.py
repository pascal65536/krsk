import hashlib
import uuid
from django.db import models
from django.conf import settings
from django.utils.safestring import mark_safe
from PIL import Image, ExifTags
from datetime import datetime
from sorl.thumbnail import get_thumbnail


def get_file_path(instance, filename):
    ext = filename.split(".")[-1]
    uid = str(uuid.uuid4()) or "JPG"
    return f"{uid[:2]}/{uid[2:4]}/{uid}.{ext.lower()}"


class Place(models.Model):
    title = models.CharField(max_length=50, unique=True, blank=False, null=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Место"
        verbose_name_plural = "Места"
        ordering = ["-title"]


class Parallel(models.Model):
    title = models.CharField(verbose_name="Название", max_length=255)
    descriptions = models.TextField(verbose_name="Описание", blank=True, null=True)
    place = models.ForeignKey(Place, blank=True, null=True, verbose_name="Место", on_delete=models.SET_NULL,)
    tags = models.CharField(verbose_name="Теги", max_length=255, blank=True, null=True)
    date_world = models.DateField(verbose_name="Дата съёмки", blank=True, null=True)

    picture = models.ImageField(verbose_name="Картинка", upload_to=get_file_path)
    image_size = models.IntegerField(verbose_name="Размер", default=0)
    content_type = models.CharField(verbose_name="Тип", max_length=255, blank=True, null=True)
    md5_hash = models.CharField(verbose_name="Хэш", max_length=255, unique=True)

    og_picture = models.CharField(verbose_name="Картинка для соцсетей", max_length=255, blank=True, null=True)
    authors = models.CharField(max_length=255, verbose_name="Автор(ы)", null=True, blank=True)
    group = models.CharField(verbose_name="Группа", max_length=255, blank=True, null=True)
    created = models.DateTimeField(verbose_name="Создано", auto_now_add=True)
    changed = models.DateTimeField(verbose_name="Изменено", auto_now=True)
    deleted = models.DateTimeField(verbose_name="Удалено", blank=True, null=True)
    meta_title = models.CharField(max_length=255, verbose_name="Title", null=True, blank=True)
    meta_keywords = models.CharField(max_length=255, verbose_name="Keywords", null=True, blank=True)
    meta_description = models.TextField(max_length=255, verbose_name="Description", null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.picture:
            return
        self.image_size = self.picture.size
        if not self.md5_hash:
            hash_md5 = hashlib.sha1()
            for chunk in self.picture.chunks():
                hash_md5.update(chunk)
            self.md5_hash = hash_md5.hexdigest()
        if hasattr(self.picture, 'file') and hasattr(self.picture.file, 'content_type'):
            self.content_type = self.picture.file.content_type
        try:
            img = Image.open(self.picture)
            exif_data = img._getexif()
            if exif_data:
                exif = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif_data.items()}
                date_str = exif.get('DateTimeOriginal') or exif.get('DateTime')
                if date_str:
                    # Формат строки: 'YYYY:MM:DD HH:MM:SS'
                    date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').date()
                    self.date_world = date_obj
        except Exception as e:
            print(f"Ошибка при чтении EXIF даты: {e}")

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
        Вывод миниатюры картинки в админке.
        """
        if not self.picture:
            return "(Нет изображения)"
        try:
            im = get_thumbnail(self.picture, '200x200', crop='center', quality=85)
            html = f'<a href="{self.picture.url}" target="_blank"><img src="{im.url}" width="200"/></a>'
            return mark_safe(html)
        except Exception as e:
            return f"(Ошибка при формировании миниатюры: {e})"

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Параллельный мир"
        verbose_name_plural = "Параллельные миры"
        ordering = ["-changed"]
