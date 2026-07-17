from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from vocab.models import CEFRLevel, Category


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


def vocab_word_detail(request, pk):
    # Stub for Task 3 — real implementation replaces only this function
    # body. This task's own template (category_word_list.html) renders
    # real Word rows through a {% url 'vocab_word_detail' word.pk %}
    # reference, which Django evaluates (and would raise NoReverseMatch
    # for) at render time if no route named vocab_word_detail exists at
    # all — a route must be registered now, at the exact path Task 3
    # specifies, so Task 3 only needs to change this function's body.
    return HttpResponse('Word detail page coming in Task 3', status=501)
