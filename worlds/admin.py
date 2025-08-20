from django.contrib import admin
from worlds.models import Place, Parallel


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ("title",)
    fieldsets = (
        (None, {"fields": ("title",)}),
    )

@admin.register(Parallel)
class ParallelAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "place", "image_img", "date_world")
    search_fields = ("title", "descriptions",)
    list_filter = ("place", "title", "authors", "group", )
    fieldsets = (
        (None, {"fields": ("picture", "title", "descriptions", "place", "tags",)}),
        ('settings', {"fields": ("group", "date_world", "authors", )}),
        ('SEO', {"fields": ("meta_title", "meta_keywords", "meta_description", "deleted", )}),
    )
