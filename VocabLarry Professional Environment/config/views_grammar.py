from django.shortcuts import get_object_or_404, render

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
    topic = get_object_or_404(GrammarTopic, slug=slug)
    blocks = topic.blocks.order_by('order')
    return render(request, 'grammar/topic_detail.html', {
        'topic': topic,
        'blocks': blocks,
    })
