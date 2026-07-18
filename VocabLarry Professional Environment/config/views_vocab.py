from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from vocab.models import CEFRLevel, Category, Word


def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    categories = Category.objects.select_related('cefr_level', 'color').order_by('order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
    })


def vocab_category(request, slug):
    category = get_object_or_404(
        Category.objects.select_related('cefr_level', 'color'), slug=slug
    )
    words = category.words.order_by('order')
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'vocab/category_word_list.html', {
        'category': category,
        'page_obj': page_obj,
    })


@ensure_csrf_cookie
def vocab_word_detail(request, pk):
    word = get_object_or_404(
        Word.objects.select_related('category', 'cefr_level'), pk=pk
    )
    learn_state = None
    if request.user.is_authenticated:
        learn_state = request.user.learn_map.get(str(word.pk))
    return render(request, 'vocab/word_detail.html', {
        'word': word,
        'learn_state': learn_state,
    })


def vocab_quiz_setup(request):
    categories = Category.objects.order_by('order')
    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/quiz_setup.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
    })


def vocab_quiz_play(request):
    # Stub for Task 2 — real implementation replaces only this function
    # body. Registered now, at the exact path Task 2 specifies, because
    # quiz_setup.html's <form action="{% url 'vocab_quiz_play' %}"> is
    # evaluated at render time regardless of whether the form is submitted.
    return HttpResponse('Quiz play page coming in Task 2', status=501)
