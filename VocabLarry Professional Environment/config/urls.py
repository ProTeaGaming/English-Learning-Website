from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.views import home

urlpatterns = [
    path('', home, name='home'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
