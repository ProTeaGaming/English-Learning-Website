from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

_ROLE_ORDER = {'user': 0, 'staff': 1, 'admin': 2}


def role_required(min_role: str):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            user_level = _ROLE_ORDER.get(getattr(request.user, 'role', 'user'), 0)
            required_level = _ROLE_ORDER.get(min_role, 99)
            if user_level < required_level:
                return HttpResponseForbidden('Access denied.')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
