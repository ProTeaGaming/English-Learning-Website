import json
import pathlib
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


class Command(BaseCommand):
    help = 'Seed grammar topics from grammar-content.json. Idempotent (upsert by slug).'

    def add_arguments(self, parser):
        parser.add_argument('--file', default=None,
                            help='Path to grammar JSON (default: <project root>/grammar-content.json)')

    def handle(self, *args, **options):
        path = pathlib.Path(options['file']) if options['file'] \
            else pathlib.Path(__file__).resolve().parents[3] / 'grammar-content.json'
        if not path.exists():
            raise CommandError(f'Grammar content file not found: {path}')
        topics = json.loads(path.read_text(encoding='utf-8'))
        valid_stages = {s for s, _ in GrammarTopic.STAGES}

        with transaction.atomic():
            for order, t in enumerate(topics):
                if t['stage'] not in valid_stages:
                    raise CommandError(
                        f"Topic '{t['slug']}' has unknown stage '{t['stage']}'"
                    )
                topic, _ = GrammarTopic.objects.update_or_create(
                    slug=t['slug'],
                    defaults={
                        'title': t['title'], 'tag': t['tag'], 'cefr_label': t['cefr'],
                        'blurb': t['blurb'], 'stage': t['stage'], 'order': order,
                    },
                )
                topic.blocks.all().delete()
                for i, b in enumerate(t['lesson']):
                    GrammarLessonBlock.objects.create(
                        topic=topic, type=b['type'], title=b.get('title', ''),
                        body=b.get('body', ''), data=b.get('data', {}), order=i,
                    )
                topic.questions.all().delete()
                for i, q in enumerate(t['quiz']):
                    GrammarQuestion.objects.create(
                        topic=topic, qtype=q['qtype'], prompt=q['prompt'],
                        options=q.get('options', []), answers=q['answers'],
                        why=q['why'], order=i,
                    )

        self.stdout.write(self.style.SUCCESS(
            f'Done. Grammar topics: {GrammarTopic.objects.count()}, '
            f'blocks: {GrammarLessonBlock.objects.count()}, '
            f'questions: {GrammarQuestion.objects.count()}'
        ))
