from django.shortcuts import render
from django.http import HttpResponse

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
    # Stub for Task 2 - will be replaced with full implementation
    return HttpResponse('Category page coming in Task 2', status=501)
