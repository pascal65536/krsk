from django.contrib import admin
from photo.models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "image_img", "created", "image_size", "content_type")
    search_fields = ("title",)
    list_filter = ("image_size", "created",)
    fieldsets = (
        (None, {"fields": ("title", "description", "picture")}),
        ("settings", {"fields": ("deleted",)}),
    )
