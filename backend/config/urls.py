"""Root URL configuration.

All REST endpoints are namespaced under ``/api/`` and delegated to the ``api``
app, which aggregates every domain module's routes. This keeps the public API
surface defined in one place and makes versioning straightforward.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

# Serve uploaded media in development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
