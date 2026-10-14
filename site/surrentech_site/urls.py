from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("manage-console/", admin.site.urls),
    path("", include("website.urls")),
]
