"""tidding URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from article.views import (
    post_detail,
    post_list,
    PostFeed,
    check_content,
    tagging,
    get_file,
    PostSitemap,
)
from worlds.views import worlds_list, worlds_group, worlds_detail


handler403 = "photo.views.tr_handler403"
handler404 = "photo.views.tr_handler404"
handler500 = "photo.views.tr_handler500"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", post_list, name="post_list"),
    path("detail/<int:pk>/", post_detail, name="post_detail"),
    path("worlds/", worlds_list, name="worlds_list"),
    path("check/<int:pk>/", check_content, name="check_content"),
    path("tagging/<int:pk>/", tagging, name="tagging"),
    path("feed/", PostFeed()),
    path("worlds_group/", worlds_group, name="worlds_group"),
    path('worlds/<int:pk>/', worlds_detail, name='worlds_detail'),
    path("<filename>.txt", get_file, name="get_file"),
    path("summernote/", include("django_summernote.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"posts": PostSitemap}},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.views.static import serve
from django.urls import re_path

urlpatterns += [
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
