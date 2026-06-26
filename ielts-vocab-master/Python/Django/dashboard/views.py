from django.shortcuts import render
from accounts.decorators import role_required
from django.contrib.auth import get_user_model
from vocab.models import Word, Category, CEFRLevel, Color


@role_required('staff')
def index(request):
    context = {
        'word_count':     Word.objects.count(),
        'category_count': Category.objects.count(),
        'cefr_count':     CEFRLevel.objects.count(),
        'color_count':    Color.objects.count(),
        'user_count':     get_user_model().objects.count(),
    }
    return render(request, 'dashboard/index.html', context)
