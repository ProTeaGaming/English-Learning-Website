from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from vocab.models import GrammarTopic


def grammar_browse(request):
    query = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    topics = GrammarTopic.objects.order_by('order')
    if query:
        topics = topics.filter(title__icontains=query)
    if stage_filter:
        topics = topics.filter(stage=stage_filter)
    topics = list(topics)
    grammar_map = request.user.grammar_map if request.user.is_authenticated else {}
    for topic in topics:
        topic.grammar_status = grammar_map.get(topic.slug)
    return render(request, 'grammar/browse.html', {
        'topics': topics,
        'stages': GrammarTopic.STAGES,
        'query': query,
        'stage_filter': stage_filter,
    })


def grammar_topic_detail(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    blocks = topic.blocks.order_by('order')
    grammar_status = None
    if request.user.is_authenticated:
        grammar_status = request.user.grammar_map.get(topic.slug)
    return render(request, 'grammar/topic_detail.html', {
        'topic': topic,
        'blocks': blocks,
        'grammar_status': grammar_status,
    })


@ensure_csrf_cookie
def grammar_topic_quiz(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    return render(request, 'grammar/topic_quiz.html', {'topic': topic})


def grammar_test_setup(request):
    return render(request, 'grammar/test_setup.html', {'stages': GrammarTopic.STAGES})


def grammar_test_play(request):
    return render(request, 'grammar/test_play.html')
