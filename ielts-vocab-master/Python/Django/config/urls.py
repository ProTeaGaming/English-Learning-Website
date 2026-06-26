import os
from django.contrib import admin
from django.http import FileResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def serve_vocab(request, **kwargs):
    # ensure_csrf_cookie forces get_token(request), so Django sets the
    # csrftoken cookie even though FileResponse never touches it itself.
    # The SPA reads that cookie (getCsrf) to authorise its POSTs.
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vocab-master.html')
    return FileResponse(open(html_path, 'rb'), content_type='text/html')


urlpatterns = [
    path('', serve_vocab),
    # allauth emails link to these; the SPA inspects the URL and drives the
    # matching headless flow (email verification / password reset).
    path('verify-email/<str:key>/', serve_vocab),
    path('reset-password/<str:key>/', serve_vocab),
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
