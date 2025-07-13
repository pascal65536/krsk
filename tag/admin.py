from tag.models import Tag
from django.contrib import admin


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
    list_filter = ()
    fieldsets = ()
