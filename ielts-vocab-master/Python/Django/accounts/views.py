import json
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

User = get_user_model()


def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in.'}, status=401)
    return None


@require_http_methods(['GET', 'POST'])
def sync(request):
    err = _require_auth(request)
    if err:
        return err
    if request.method == 'GET':
        return JsonResponse({'learn_map': request.user.learn_map})
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    request.user.learn_map = body.get('learn_map', {})
    request.user.save(update_fields=['learn_map'])
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
    return JsonResponse({'ok': True})


@require_http_methods(['POST'])
def delete_account(request):
    err = _require_auth(request)
    if err:
        return err
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
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
    body = json.loads(request.body or '{}')
    email = body.get('email', '').strip().lower()
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
