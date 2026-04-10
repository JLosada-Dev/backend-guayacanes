from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/core/',    include('apps.core.urls')),
    path('api/v1/urbaser/', include('apps.infra_servicios_publicos_urbaser.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
