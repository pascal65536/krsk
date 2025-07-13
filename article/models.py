from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from krasnoarsk.utils import cyr2lat, opengraph
from article.managers import PostManager
from photo.models import Photo
from tag.models import Tag
from django.conf import settings


class Category(models.Model):
    color_tuple = [
        ("bg-info", "info"),
        ("bg-dark", "dark"),
        ("bg-light", "light"),
        ("bg-danger", "danger"),
        ("bg-primary", "primary"),
        ("bg-success", "success"),
        ("bg-warning", "warning"),
        ("bg-secondary", "secondary"),
    ]
    title = models.CharField(verbose_name="Название", max_length=20)
    lead = models.TextField(verbose_name="Лидер-абзац", blank=True, null=True)
    parent_id = models.IntegerField(verbose_name="Родительская категория", default=0)
    order = models.IntegerField(verbose_name="Сортировка", default=1)
    slug = models.CharField(verbose_name="Slug", max_length=20)
    is_menu = models.BooleanField(verbose_name="Показывать в меню", default=False)
    color = models.CharField(choices=color_tuple, max_length=255, verbose_name="Цвет")

    image = models.ForeignKey(
        Photo, blank=True, null=True, verbose_name="Photo", on_delete=models.SET_NULL
    )
    og_picture = models.CharField(
        verbose_name="Картинка для соцсетей", max_length=255, blank=True
    )
    created = models.DateTimeField(verbose_name="Создано", auto_now_add=True)
    changed = models.DateTimeField(verbose_name="Изменено", auto_now=True)
    deleted = models.DateTimeField(verbose_name="Удалено", blank=True, null=True)
    meta_title = models.CharField(
        max_length=255, verbose_name="Title", null=True, blank=True
    )
    meta_keywords = models.CharField(
        max_length=255, verbose_name="Keywords", null=True, blank=True
    )
    meta_description = models.TextField(
        max_length=255, verbose_name="Description", null=True, blank=True
    )

    def image_img(self):
        """
        Вывод картинок в админке
        """
        if not self.image:
            return "(Нет изображения)"
        html = [
            f'<a href="{self.image.picture.url}" target="_blank">',
            f'<img src="{self.image.picture.url}" width="100"/></a>',
        ]
        return mark_safe("".join(html))

    def save(self, *args, **kwargs):
        self.slug = cyr2lat(self.title)
        if self.pk:
            self.og_picture = opengraph(self)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Название раздела"
        verbose_name_plural = "Названия разделов"
        ordering = ["-order"]


class Post(models.Model):
    title = models.CharField(verbose_name="Заголовок поста", max_length=255)
    lead = models.TextField(verbose_name="Лидер-абзац", blank=True, null=True)
    text = models.TextField(verbose_name="Текст поста", blank=True, null=True)
    category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        verbose_name="Раздел",
        on_delete=models.SET_NULL,
    )
    tag = models.ManyToManyField(Tag, verbose_name="Тег", blank=True)
    date_post = models.DateTimeField(verbose_name="Дата публикации")
    view = models.IntegerField(verbose_name="Яндекс.метрика", default=0)
    plagiarism = models.FloatField(verbose_name="Плагиат", default=0)
    plagiarism_json = models.JSONField(
        verbose_name="Результат проверки на плагиат", blank=True, null=True
    )
    image = models.ForeignKey(
        Photo, blank=True, null=True, verbose_name="Photo", on_delete=models.SET_NULL
    )
    og_picture = models.CharField(
        verbose_name="Картинка для соцсетей", max_length=255, blank=True, null=True
    )
    authors = models.CharField(
        max_length=255, verbose_name="Автор(ы)", null=True, blank=True
    )
    created = models.DateTimeField(verbose_name="Создано", auto_now_add=True)
    changed = models.DateTimeField(verbose_name="Изменено", auto_now=True)
    deleted = models.DateTimeField(verbose_name="Удалено", blank=True, null=True)
    meta_title = models.CharField(
        max_length=255, verbose_name="Title", null=True, blank=True
    )
    meta_keywords = models.CharField(
        max_length=255, verbose_name="Keywords", null=True, blank=True
    )
    meta_description = models.TextField(
        max_length=255, verbose_name="Description", null=True, blank=True
    )

    objects = PostManager()


    @property
    def url_og_picture(self):
        return settings.PROTO_DOMAIN + '/' + self.og_picture

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"pk": self.pk})

    def image_img(self):
        """
        Вывод картинок в админке
        """
        if not self.image:
            return "(Нет изображения)"
        html = [
            f'<a href="{self.image.picture.url}" target="_blank">',
            f'<img src="{self.image.picture.url}" width="100"/></a>',
        ]
        return mark_safe("".join(html))

    @classmethod
    def update_qs(cls, post_qs):
        for post in post_qs:
            if post.image:
                post.image_picture = post.image.picture
            post.category_title = post.category.title
            post.category_slug = post.category.slug
        return post_qs

    def save(self, *args, **kwargs):       
        if self.pk:
            self.og_picture = opengraph(self)
        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Запись в блог"
        verbose_name_plural = "Записи в блог"
        ordering = ["-date_post"]
