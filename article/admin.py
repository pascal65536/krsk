from django.contrib import admin

from article.models import Post, Category
from django_summernote.admin import SummernoteModelAdmin


@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):
    summernote_fields = ("text",)
    autocomplete_fields = ("image", "tag")
    search_fields = ["title", "text", "lead", "authors", ]
    list_display = (
        "id",
        "title",
        "image_img",
        "category",
        "date_post",
        "deleted",
        "plagiarism",
        "view",
    )
    list_filter = ("date_post", "plagiarism", "category", "authors", )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "lead",
                    "text",
                    "category",
                    "date_post",
                    "image",
                    "tag",
                )
            },
        ),
        ("plagiarism", {"fields": ("plagiarism", "plagiarism_json", "authors")}),
        ("SEO", {"fields": ("meta_title", "meta_keywords", "meta_description")}),
        ("settings", {"fields": ("deleted",)}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "image_img", "order", "slug", "is_menu")
    list_filter = ("order", "is_menu", "color")
    fieldsets = (
        (None, {"fields": ("title", "lead", "order", "image", "is_menu", "color")}),
        ("SEO", {"fields": ("meta_title", "meta_keywords", "meta_description")}),
        ("settings", {"fields": ("deleted",)}),
    )
