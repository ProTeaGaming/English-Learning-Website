import os
from django.contrib import admin
from django.http import FileResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def serve_vocab(request):
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vocab-master.html')
    return FileResponse(open(html_path, 'rb'), content_type='text/html')


urlpatterns = [
    path('', serve_vocab),
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
