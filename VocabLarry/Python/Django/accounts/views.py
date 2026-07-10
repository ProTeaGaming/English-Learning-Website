import json
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .decorators import is_staff_user

User = get_user_model()


def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in.'}, status=401)
    return None


def _picture_url(request, user):
    if user.picture:
        return request.build_absolute_uri(user.picture.url)
    return ''


@require_http_methods(['GET'])
def session(request):
    if not request.user.is_authenticated:
        return JsonResponse({'loggedIn': False})
    u = request.user
    return JsonResponse({
        'loggedIn': True,
        'id': u.pk,
        'name': u.name,
        'username': u.username,
        'email': u.email,
        'picture': _picture_url(request, u),
        'isStaff': is_staff_user(u),
        'hasPassword': u.has_usable_password(),
    })


@require_http_methods(['GET', 'POST'])
def sync(request):
    err = _require_auth(request)
    if err:
        return err
    if request.method == 'GET':
        return JsonResponse({'learn_map': request.user.learn_map,
                             'grammar_map': request.user.grammar_map})
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    request.user.learn_map = body.get('learn_map', {})
    fields = ['learn_map']
    # Absent key leaves grammar_map untouched so a stale tab still posting the
    # old learn_map-only payload can't wipe the account's grammar progress.
    if 'grammar_map' in body:
        request.user.grammar_map = body['grammar_map']
        fields.append('grammar_map')
    request.user.save(update_fields=fields)
    return JsonResponse({'ok': True})


@require_http_methods(['POST'])
def update_profile(request):
    err = _require_auth(request)
    if err:
        return err
    user = request.user
    name = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()

    if name:
        if len(name) > 60:
            return JsonResponse({'error': 'Name too long (max 60 chars).'}, status=400)
        user.name = name

    if username:
        if not (3 <= len(username) <= 20) or not username.isalnum():
            return JsonResponse(
                {'error': 'Username must be 3–20 alphanumeric characters.'}, status=400
            )
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            return JsonResponse({'error': 'Username already taken.'}, status=409)
        user.username = username

    if 'picture' in request.FILES:
        f = request.FILES['picture']
        if f.size > 2 * 1024 * 1024:
            return JsonResponse({'error': 'Image must be under 2 MB.'}, status=400)
        if user.picture:
            user.picture.delete(save=False)
        user.picture = f

    user.save()
    return JsonResponse({'ok': True, 'picture': _picture_url(request, user)})


@require_http_methods(['POST'])
def delete_account(request):
    err = _require_auth(request)
    if err:
        return err
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    # Google/social-only accounts have no usable password (allauth sets an
    # unusable hash) — check_password() would reject every input for them,
    # permanently blocking self-service deletion, so only require it when
    # the account actually has a password to verify.
    if request.user.has_usable_password():
        password = body.get('password', '')
        if not request.user.check_password(password):
            return JsonResponse({'error': 'Incorrect password.'}, status=401)
    if request.user.picture:
        request.user.picture.delete(save=False)
    request.user.delete()
    request.session.flush()
    return JsonResponse({'ok': True})


@csrf_exempt
@require_http_methods(['POST'])
def check_email(request):
    try:
        data = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    email = data.get('email', '').strip().lower()
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
