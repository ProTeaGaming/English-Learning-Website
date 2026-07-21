import django.db.models.deletion
from django.db import migrations, models

SECTIONS = [
    ('tenses', 'Tenses', 'i-clock',
     ['1501139083538-0139583c060f', '1456513080510-7bf3a84b82f8']),
    ('questions-reported-speech', 'Questions & Reported Speech', 'i-message',
     ['1543269865-cbf427effbad', '1504711434969-e33886168f5c']),
    ('nouns-pronouns-determiners', 'Nouns, Pronouns & Determiners', 'i-type',
     ['1507842217343-583bb7270b66', '1524995997946-a1c2e315a42f']),
    ('adjectives-adverbs', 'Adjectives & Adverbs', 'i-palette',
     ['1474932430478-367dbb6832c1', '1516979187457-637abb4f9353']),
    ('word-forms-prepositions', 'Word Forms & Prepositions', 'i-puzzle',
     ['1457369804613-52c61a468e7d', '1488190211105-8b0e65b80b4e']),
    ('verb-patterns-modals', 'Verb Patterns & Modals', 'i-activity',
     ['1455390582262-044cdead277a', '1434030216411-0b793f4b4173']),
    ('voice', 'Voice', 'i-megaphone',
     ['1478737270239-2f02b77fc618', '1470229722913-7c0e2dbbafd3']),
    ('conditionals-unreal-forms', 'Conditionals & Unreal Forms', 'i-dice',
     ['1529699211952-734e80c4d42b', '1522069169874-c58ec4b76be5']),
    ('clauses', 'Clauses', 'i-link',
     ['1433086966358-54859d0ed716', '1481627834876-b7833e8f5570']),
    ('emphasis-sentence-focus', 'Emphasis & Sentence Focus', 'i-target',
     ['1470229722913-7c0e2dbbafd3', '1450101499163-c8848c66ca85']),
    ('cohesion-academic-style', 'Cohesion & Academic Style', 'i-scroll',
     ['1481627834876-b7833e8f5570', '1450101499163-c8848c66ca85']),
    ('idioms', 'Idioms', 'i-masks',
     ['1474932430478-367dbb6832c1', '1456513080510-7bf3a84b82f8']),
]

TOPIC_SECTIONS = {
    'present-simple-continuous': 'Tenses',
    'past-simple-continuous': 'Tenses',
    'future-forms': 'Tenses',
    'perfect-tenses': 'Tenses',
    'question-forms': 'Questions & Reported Speech',
    'reported-speech': 'Questions & Reported Speech',
    'question-tags-indirect': 'Questions & Reported Speech',
    'nouns-plurals': 'Nouns, Pronouns & Determiners',
    'pronouns-possessives': 'Nouns, Pronouns & Determiners',
    'articles': 'Nouns, Pronouns & Determiners',
    'quantifiers': 'Nouns, Pronouns & Determiners',
    'comparatives-superlatives': 'Adjectives & Adverbs',
    'gradable-adjectives': 'Adjectives & Adverbs',
    'adverbs-word-order': 'Adjectives & Adverbs',
    'word-forms': 'Word Forms & Prepositions',
    'prepositions-time-place': 'Word Forms & Prepositions',
    'gerunds-infinitives': 'Verb Patterns & Modals',
    'used-to': 'Verb Patterns & Modals',
    'modal-verbs': 'Verb Patterns & Modals',
    'advanced-modality': 'Verb Patterns & Modals',
    'passive-voice': 'Voice',
    'causatives': 'Voice',
    'conditionals': 'Conditionals & Unreal Forms',
    'mixed-conditionals': 'Conditionals & Unreal Forms',
    'wish-if-only': 'Conditionals & Unreal Forms',
    'subjunctive-unreal-past': 'Conditionals & Unreal Forms',
    'relative-clauses': 'Clauses',
    'participle-clauses': 'Clauses',
    'inversion-emphasis': 'Emphasis & Sentence Focus',
    'cleft-sentences': 'Emphasis & Sentence Focus',
    'fronting-ever-clauses': 'Emphasis & Sentence Focus',
    'dummy-subjects': 'Emphasis & Sentence Focus',
    'linking-words': 'Cohesion & Academic Style',
    'ellipsis-substitution': 'Cohesion & Academic Style',
    'nominalisation': 'Cohesion & Academic Style',
    'hedging-academic-tone': 'Cohesion & Academic Style',
    'irregular-verbs': 'Tenses',
    'conjunctions': 'Clauses',
    'phrasal-verbs': 'Verb Patterns & Modals',
    'dependent-prepositions': 'Word Forms & Prepositions',
    'make-let-verb-patterns': 'Verb Patterns & Modals',
    'comparison-structures': 'Adjectives & Adverbs',
    'impersonal-passive': 'Voice',
    'subject-verb-agreement': 'Nouns, Pronouns & Determiners',
    'everyday-idioms': 'Idioms',
    'conversational-idioms': 'Idioms',
    'advanced-formal-idioms': 'Idioms',
}


def seed_and_backfill(apps, schema_editor):
    GrammarSection = apps.get_model('vocab', 'GrammarSection')
    GrammarTopic = apps.get_model('vocab', 'GrammarTopic')

    sections_by_name = {}
    for order, (slug, name, icon, image_ids) in enumerate(SECTIONS):
        section = GrammarSection.objects.create(
            slug=slug, name=name, icon=icon, order=order, image_ids=image_ids,
        )
        sections_by_name[name] = section

    for topic in GrammarTopic.objects.all():
        section_name = TOPIC_SECTIONS.get(topic.slug, topic.tag)
        section = sections_by_name.get(section_name)
        if section:
            topic.section = section
            topic.save(update_fields=['section'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0008_remove_us_uk_new_words'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrammarSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('icon', models.CharField(max_length=30)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('image_ids', models.JSONField(blank=True, default=list)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='grammartopic',
            name='section',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='topics', to='vocab.grammarsection',
            ),
        ),
        migrations.RunPython(seed_and_backfill, reverse_code=noop),
    ]
