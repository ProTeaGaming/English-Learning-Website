from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
