# Proxy models so the grammar tables (which live in the vocab app) get their
# own "Grammar" section in the Django admin. No new tables are created.
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


class Topic(GrammarTopic):
    class Meta:
        proxy = True
        ordering = ['order']


class LessonBlock(GrammarLessonBlock):
    class Meta:
        proxy = True
        ordering = ['order']


class Question(GrammarQuestion):
    class Meta:
        proxy = True
        ordering = ['order']
