from django.contrib.sitemaps import Sitemap
from .models import Parallel

class ParallelSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return Parallel.objects.filter(deleted__isnull=True)

    def lastmod(self, obj):
        return obj.changed