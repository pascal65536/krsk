import os
import pymorphy3
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from article.models import Post, Category
from django.utils import timezone
from django.db.models import Count
from photo.models import Photo
from tag.models import Tag
from django.contrib.sitemaps import Sitemap
from django.contrib.syndication.views import Feed
from krasnoarsk.utils import check_plagiarism


morph = pymorphy3.MorphAnalyzer()


def get_morphy_word(word):
    p = morph.parse(word)[0]
    return p.normal_form


@login_required(login_url="/login/")
@staff_member_required
def tagging(request, pk):
    """
    Установка тегов
    """
    russian = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

    post = get_object_or_404(Post, pk=pk)

    if not request.method == "POST":
        return redirect(post_detail, post.pk)

    post.tag.clear()
    post_lst = list(filter(None, [post.text, post.lead, post.title, post.authors]))

    text = " ".join(post_lst)
    text = "".join([z if z in russian else " " for z in text.lower()])
    text_lst = sorted(set([z for z in text.lower().split() if len(z) > 2]))
    if len(text_lst) < 20:
        return redirect(post_detail, post.pk)

    for word in text_lst:
        normal = get_morphy_word(word)
        if not Tag.objects.filter(title=normal).count():
            tag = Tag()
            tag.title = normal
            tag.save()
        else:
            tag = Tag.objects.get(title=normal)
        if tag not in post.tag.all():
            post.tag.add(tag)
    post.save()

    params = dict(request.GET)
    return HttpResponseRedirect(reverse("post_detail", args=[post.pk]))


def post_list(request):
    """
    Список постов
    """
    tag_title = request.GET.get("tag")
    category = request.GET.get("category")
    offset = int(request.GET.get("offset", "0"))
    post_qs = Post.objects.for_user(request.user)
    message = "Последние новости"
    if tag_title:
        message = f'Последние новости по тегу "{tag_title}"'
        tag = get_object_or_404(Tag, title=tag_title)
        post_qs = post_qs.filter(tag=tag)
    if category:
        category_obj = Category.objects.filter(slug=category).last()
        message = f'Последние новости в категории "{category_obj.title}"'
        post_qs = post_qs.filter(category__slug=category)
    count = post_qs.count()
    post_qs = post_qs[offset : offset + 16]

    category_dct = dict(Category.objects.values_list("id", "title"))
    # for post in post_qs:
    #     post.category_name = category_dct[post.category_id]
    #     post.has_image = bool(post.image)

    page_lst = list()
    page_lst.append(0)
    page_lst.append(count // 16)
    page_lst.append(count - 1)
    page_lst.append(offset)
    page_lst.append(offset + 16)
    page_lst.append(offset - 16)
    page_lst = [p for p in set(page_lst) if 0 <= p <= count]
    page_lst.sort()

    params = dict(request.GET)
    return render(
        request,
        "article/post_list.html",
        {
            "post_qs": post_qs,
            "page_lst": page_lst,
            "message": message,
            "request": request,
            "category": category,
        },
    )


@login_required(login_url="/login/")
@staff_member_required
def check_content(request, pk):
    """
    Проверка на плагиат
    """
    post = get_object_or_404(Post, pk=pk)

    if not request.method == "POST":
        return redirect(post_detail, post.pk)

    result_dct = check_plagiarism(post.text)
    post.plagiarism = result_dct.get("percent")
    post.plagiarism_json = result_dct.get("matches")
    if float(result_dct["percent"]) > 20:
        post.deleted = None
    post.save()

    params = dict(request.GET)
    return HttpResponseRedirect(reverse("post_detail", args=[post.pk]))


def post_detail(request, pk):
    """
    Детали поста
    """
    post = get_object_or_404(Post, pk=pk)

    category_dct = dict(Category.objects.values_list("id", "title"))
    post.has_image = bool(post.image)
    post.category_name = category_dct[post.category_id]
    tag_lst = list()
    for tag in post.tag.all():
        tag_lst.append(tag.title)

    post.view += 1
    post.save()

    params = dict(request.GET)
    return render(
        request,
        "article/post_detail.html",
        {
            "post": post,
            "tag_lst": tag_lst,
        },
    )


def get_file(request, filename):
    file_path = f"{filename}.txt"

    params = dict(request.GET)
    if os.path.exists(f"templates/{file_path}"):
        return render(request, file_path, content_type="text/plain")
    else:
        raise Http404("non file")


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        post_qs = Post.objects.filter(deleted__isnull=True)
        post_qs = post_qs.filter(date_post__lte=timezone.now())
        return post_qs

    def location(self, obj):
        return reverse("post_detail", args=[obj.pk])

    def lastmod(self, obj):
        return obj.changed


class PostFeed(Feed):
    title = settings.TITLE
    link = "/"
    # description = "Последние опубликованные посты"

    def items(self):
        post_qs = Post.objects.filter(
            deleted__isnull=True, date_post__lte=timezone.now()
        )
        return post_qs.order_by("-date_post")[:50]

    def item_title(self, obj):
        return obj.title

    def item_description(self, obj):
        return obj.lead

    def item_link(self, obj):
        return reverse("post_detail", args=[obj.pk])

    def item_pubdate(self, obj):
        return obj.date_post

    def item_updateddate(self, obj):
        return timezone.now()

    def item_enclosure_url(self, obj):
        if obj.og_picture:
            return obj.url_og_picture
        return None

    # def item_enclosure_length(self, obj):
    #     if obj.og_picture:
    #         return obj.og_picture.size
    #     return None

    # def item_enclosure_mime_type(self, obj):
    #     if obj.image:
    #         return obj.image.content_type
    #     return None
