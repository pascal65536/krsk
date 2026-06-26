from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from .models import Post, Category

class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Post.objects.filter(
            deleted__isnull=True,
            date_post__lte=timezone.now()
        )

    def lastmod(self, obj):
        return obj.changed


class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Category.objects.filter(deleted__isnull=True)

    def lastmod(self, obj):
        return obj.changed