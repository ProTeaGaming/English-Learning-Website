import os
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
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vocablarry.html')
    response = FileResponse(open(html_path, 'rb'), content_type='text/html')
    # FileResponse sets no Cache-Control by default, leaving this HTML GET
    # heuristically cacheable by the browser - a plain reload (not a hard
    # refresh) can then keep serving a stale copy of the whole SPA after a
    # redeploy, silently missing whatever JS fix shipped most recently while
    # older fixes already baked into that stale copy still appear to work.
    # This is a single actively-developed HTML file, not a static asset, so
    # it must always be revalidated.
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response


urlpatterns = [
    path('', serve_vocab),
    # allauth emails link to these; the SPA inspects the URL and drives the
    # matching headless flow (email verification / password reset).
    path('verify-email/<str:key>/', serve_vocab),
    path('reset-password/<str:key>/', serve_vocab),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
