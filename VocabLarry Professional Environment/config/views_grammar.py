from django.http import HttpResponse
from django.shortcuts import render

from vocab.models import GrammarTopic


def grammar_browse(request):
    query = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    topics = GrammarTopic.objects.order_by('order')
    if query:
        topics = topics.filter(title__icontains=query)
    if stage_filter:
        topics = topics.filter(stage=stage_filter)
    return render(request, 'grammar/browse.html', {
        'topics': topics,
        'stages': GrammarTopic.STAGES,
        'query': query,
        'stage_filter': stage_filter,
    })


def grammar_topic_detail(request, slug):
    # Stub for Task 2 — real implementation replaces only this function
    # body. Registered now, at the exact path Task 2 specifies, because
    # browse.html's {% url 'grammar_topic_detail' topic.slug %} is
    # evaluated at render time regardless of whether the link is clicked.
    return HttpResponse('Grammar topic detail coming in Task 2', status=501)
