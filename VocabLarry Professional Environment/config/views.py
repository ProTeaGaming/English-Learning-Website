from django.shortcuts import render

from vocab.models import Category, Word


def home(request):
    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    learned_ids = [int(k) for k, v in learn_map.items() if v == 'learned']
    started_ids = [int(k) for k in learn_map.keys()]
    total_words = Word.objects.count()
    words_learned = len(learned_ids)
    pct_complete = round(words_learned / total_words * 100) if total_words else 0
    categories_started = Category.objects.filter(words__id__in=started_ids).distinct().count()
    return render(request, 'home.html', {
        'words_learned': words_learned,
        'categories_started': categories_started,
        'pct_complete': pct_complete,
    })


def reading(request):
    return render(request, 'reading.html')


def writing(request):
    return render(request, 'writing.html')


def listening(request):
    return render(request, 'listening.html')


def speaking(request):
    return render(request, 'speaking.html')
