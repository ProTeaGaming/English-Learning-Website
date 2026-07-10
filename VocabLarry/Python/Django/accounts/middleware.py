from django.http import HttpResponseForbidden
from .decorators import ROLE_ORDER, effective_role_level


class DashboardMFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/dashboard/') and request.user.is_authenticated:
            if effective_role_level(request.user) >= ROLE_ORDER['staff']:
                from allauth.mfa.adapter import get_adapter
                adapter = get_adapter()
                if not adapter.is_mfa_enabled(request.user):
                    return HttpResponseForbidden(
                        'Dashboard requires 2FA. Enable it in your profile settings first.'
                    )
        return self.get_response(request)
