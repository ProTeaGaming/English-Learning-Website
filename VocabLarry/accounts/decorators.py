from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

ROLE_ORDER = {'user': 0, 'staff': 1, 'admin': 2}


def effective_role_level(user) -> int:
    # createsuperuser sets is_staff/is_superuser but leaves the custom `role`
    # field at its 'user' default, so both must be considered — otherwise a
    # fresh superuser is locked out of every role_required view.
    if not getattr(user, 'is_authenticated', False):
        return 0
    level = ROLE_ORDER.get(getattr(user, 'role', 'user'), 0)
    if getattr(user, 'is_superuser', False):
        level = max(level, ROLE_ORDER['admin'])
    elif getattr(user, 'is_staff', False):
        level = max(level, ROLE_ORDER['staff'])
    return level


def is_staff_user(user) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    return effective_role_level(user) >= ROLE_ORDER['staff']


def role_required(min_role: str):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            required_level = ROLE_ORDER.get(min_role, 99)
            if effective_role_level(request.user) < required_level:
                return HttpResponseForbidden('Access denied.')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
