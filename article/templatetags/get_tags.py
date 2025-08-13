from article.models import Category, Post
from django.utils import timezone
from django.conf import settings
from django import template
from django.db.models import Count, Q, QuerySet
from datetime import timedelta


register = template.Library()


@register.inclusion_tag("article/meta.html", takes_context=True)
def get_meta(context):
    """
    Выводит meta
    """
    domain = settings.PROTO_DOMAIN
    dilemeter = "|"
    url = f"{domain}{context['request'].get_full_path()}"
    link_lst = list()
    link_lst.append({"rel": "canonical", "href": url})
    path_info = context["request"].META["PATH_INFO"]

    meta_lst = list()
    meta_lst += settings.VERIFICATION_CODE
    title_lst = list()
    title_lst.append(settings.TITLE)
    keywords_lst = list()
    keywords_lst += settings.KEYWORDS
    published = None
    image = None
    description_lst = list()
    for cd in context.dicts:
        for k, v in cd.items():
            if k == "page_dct" and isinstance(v, dict):
                title_lst.append(f"Страница {v.get('num_page')} из {v.get('all_page')}")
            if k == "message" and isinstance(v, str):
                title_lst.append(v)
                description_lst.append(settings.TITLE)
                description_lst.append(v)
            if k == "post" and isinstance(v, Post):
                published = published or v.date_post.strftime(f"%Y-%m-%d %H:%M:%S")
                if v.meta_title:
                    title_lst.append(v.meta_title)
                else:
                    title_lst.append(v.title)

                description_lst = list()
                if v.meta_description:
                    description_lst.append(v.meta_description)
                else:
                    description_lst.append(v.lead)

                if v.meta_keywords:
                    keywords_lst = v.meta_keywords.split(",")
                else:
                    for tag in v.tag.all():
                        keywords_lst.append(tag.title)
                image = f"{domain}/{v.og_picture}"
            if k == "post_qs" and isinstance(v, QuerySet):
                for post in v:
                    description_lst.append(post.title)
                    for tag in post.tag.all():
                        keywords_lst.append(tag.title)

    keywords_lst = list(set(keywords_lst))
    keywords_lst = keywords_lst[:10]
    keywords = ", ".join(keywords_lst)
    meta_lst.append({"name": "keywords", "content": keywords})

    description_lst.reverse()
    if not description_lst:
        description_lst.append(settings.DESCRIPTION)
    description = ". ".join(description_lst)
    meta_lst.append({"name": "description", "content": description[:160]})
    title = f" {dilemeter} ".join(title_lst)

    # opengraph
    meta_lst.append({"name": "robots", "content": "max-image-preview:large"})
    meta_lst.append({"property": "og:url", "content": url})
    meta_lst.append({"property": "og:title", "content": title})
    meta_lst.append({"property": "og:site_name", "content": url})
    meta_lst.append({"property": "og:locale", "content": "ru-RU"})
    meta_lst.append({"property": "og:description", "content": description})
    if published:
        meta_lst.append({"property": "og:article:published_time", "content": published})
        meta_lst.append({"property": "article:published_time", "content": published})

    if image:
        og_type = "png"
        image_type = "png"
        height = 512
        width = 1024
        meta_lst.append({"property": "og:type", "content": og_type})
        meta_lst.append({"property": "og:image", "content": image})
        meta_lst.append({"property": "og:article:section", "content": ""})
        meta_lst.append({"property": "vk:image", "content": image})
        meta_lst.append({"property": "og:image:type", "content": image_type})
        meta_lst.append({"property": "og:image:width", "content": width})
        meta_lst.append({"property": "og:image:height", "content": height})

    return {
        "context": context,
        "meta_lst": meta_lst,
        "link_lst": link_lst,
        "title": title,
    }


@register.inclusion_tag("article/main_menu.html", takes_context=True)
def get_main_menu(context):
    """
    Выводит виджет меню
    """
    category_qs = Category.objects.filter(deleted__isnull=True).order_by("-order")
    category_lst = category_qs.values_list("slug", "title")
    if context.get("post"):
        active = context.get("post").category.slug
    else:
        active = context.get("request").GET.get("category")
    return {"category_lst": category_lst, "active": active, "context": context}


@register.inclusion_tag("article/footer.html", takes_context=True)
def get_footer(context):
    """
    Выводит виджет футера
    """
    category_qs = Category.objects.filter(deleted__isnull=True).order_by("-order")
    category_lst = category_qs.values_list("slug", "title")
    return {
        "category_lst": category_lst,
        "description": settings.DESCRIPTION,
        "title": settings.TITLE,
        "context": context,
    }


@register.inclusion_tag("article/populate.html", takes_context=True)
def get_populate_qs(context):
    """
    Популярные посты
    """
    category = context.get("category")
    post_obj = context.get("post")
    populate_qs = Post.objects.for_user()
    if post_obj:
        populate_qs = populate_qs.exclude(id=post_obj.id)
        populate_qs = populate_qs.exclude(category=post_obj.category)
    elif category:
        populate_qs = populate_qs.exclude(category__slug=category)
    populate_qs = populate_qs.filter(
        date_post__gte=(timezone.now() - timedelta(weeks=12))
    )
    populate_qs = populate_qs.order_by("-view")[:20]
    category_dct = dict(Category.objects.values_list("id", "title"))
    for post in populate_qs:
        post.category_name = category_dct[post.category_id]
        post.has_image = bool(post.image)
    return {"populate_qs": populate_qs, "context": context}


@register.inclusion_tag("article/category.html", takes_context=True)
def get_similar_qs(context):
    """
    Посты близкие по тегам
    """
    news = context.get("post")
    populate_qs = Post.objects.for_user()

    tag_dct = dict()
    for tag in news.tag.all():
        for pk in populate_qs.filter(tag=tag).values_list('id', flat=True):
            tag_dct.setdefault(pk, 0)
            tag_dct[pk] += 1
    tag_lst = list()
    for k, v in tag_dct.items():
        tag_lst.append((v, k))

    res = sorted(tag_lst, reverse=True)

    pk_lst = [z[1] for z in res[:25] if z[1] != news.id]
    pk_lst = pk_lst[:24]

    populate_qs = Post.objects.filter(pk__in=pk_lst)
    category_dct = dict(Category.objects.values_list("id", "title"))
    for post in populate_qs:
        post.category_name = category_dct[post.category_id]
        post.has_image = bool(post.image)

    return {
        "populate_qs": populate_qs,
    }