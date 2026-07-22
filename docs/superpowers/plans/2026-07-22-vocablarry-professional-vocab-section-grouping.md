# VocabLarry Professional Environment — Vocabulary Category Section Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the deferred 75-section grouping layer (10 basic/27 intermediate/38 advanced tiers, 250 categories) to the Vocabulary Category browse page, plus a small section-aware header upgrade to the category word-list drill-in page.

**Architecture:** Four sequential tasks. Task 1 adds the `VocabSection` model, the `Category.section` FK, and one migration seeding all 75 sections + backfilling all 250 category assignments from a verified, literal data set (no new view/template code, verified by running the migration directly and spot-checking the result — this project's `--no-migrations` pytest setting means the migration's `RunPython` step is invisible to the automated suite, matching the established precedent from `GrammarSection`'s own migration). Task 2 relocates two CSS component families (`.section-block`, `.cat-view-*`) from `grammar.css` to `base.css` as shared infrastructure (Grammar built them first; Vocab now needs the identical components) and renames the tiny generic accordion-toggle script from `grammar-browse.js` to `section-accordion.js` — a pure relocation/rename, zero behavior or visual change, verified by the full suite staying green. Task 3 rewrites the `vocab_browse` view and `browse.html` template to render paginated section accordions with the new Tier filter. Task 4 adds the section-aware header to `category_word_list.html`.

**Tech Stack:** Django templates, server-side ORM filtering (no client-side JS filtering beyond the existing generic accordion toggle), plain CSS (existing custom-property/component system), pytest + Django test client.

## Global Constraints

- Only files under `VocabLarry Professional Environment/` may be modified. `VocabLarry/` (production) is read-only reference material.
- All filtering (`q`, `cefr`, `progress`, new `tier`) is server-side via GET query params and plain `<a href>`/`<form method="get">` — no client-side JS filtering logic. The only client-side JS in this whole plan is the existing generic accordion open/close toggle (relocated, not rewritten).
- `pytest.ini` sets `addopts = --no-migrations` — the migration's `RunPython` seeding/backfill will NOT execute in any test's database. Every test needing section data creates its own `VocabSection`/`Category.section` fixture rows directly. Task 1's own verification is therefore NOT a pytest task — it's a manual `manage.py migrate` + shell spot-check, matching the established precedent from `GrammarSection`'s migration (`vocab/migrations/0009_grammarsection.py`).
- `VocabSection` mirrors `GrammarSection`'s shape but without `icon`/`image_ids` (confirmed unnecessary — production's vocab section headers render only a numeral, name, meta text, and progress, no icon/image).
- A section with zero categories remaining after `q`/`cefr`/`progress` filtering is entirely absent from the results (matches production).
- The synthetic "CEFR Levels" pseudo-section/pseudo-category feature (production's 5th headline tab) is explicitly out of scope — do not build any part of it.
- No change to Grammar Browse's own behavior, markup, or visual appearance — Task 2's CSS/JS relocation must be behavior-identical, verified by the existing Grammar Browse tests staying green untouched.

---

### Task 1: `VocabSection` model, `Category.section` FK, and the seed/backfill migration

**Files:**
- Modify: `VocabLarry Professional Environment/vocab/models.py` (add `VocabSection`, add `section` field to `Category`)
- Create: `VocabLarry Professional Environment/vocab/migrations/0010_vocabsection.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `VocabSection(slug, name, tier, order)` and `Category.section` (nullable FK, `related_name='categories'`) — Tasks 3/4 read `category.section.name`, `category.section.tier`, and query/order by `section__order`.

- [ ] **Step 1: Add the `VocabSection` model and `Category.section` field**

In `VocabLarry Professional Environment/vocab/models.py`, add this model directly after the existing `Category` model definition:

```python
class VocabSection(models.Model):
    TIERS = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    slug  = models.SlugField(max_length=100, unique=True)
    name  = models.CharField(max_length=100)
    tier  = models.CharField(max_length=12, choices=TIERS)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name
```

Then add a `section` field to the existing `Category` model (directly after its `color` field):

```python
    section = models.ForeignKey(
        VocabSection, null=True, blank=True, on_delete=models.SET_NULL, related_name='categories',
    )
```

`VocabSection` must be defined BEFORE `Category` in the file if `Category` references it directly by name — since `VocabSection` is being added after `Category` per the instruction above, use the string reference `'VocabSection'` in the FK instead: `models.ForeignKey('VocabSection', null=True, blank=True, on_delete=models.SET_NULL, related_name='categories')`. (Django resolves string references at app-loading time regardless of declaration order in the file, so this works either way — using the string form avoids needing to reorder the file.)

- [ ] **Step 2: Create the migration file directly**

Create `VocabLarry Professional Environment/vocab/migrations/0010_vocabsection.py` with the complete content below — this migration is hand-authored in full (schema operations plus the literal seed data in the same `RunPython` step), not generated via `makemigrations`, since it needs to carry the verified seed data that no auto-detection could produce.

Replace the entire contents of `VocabLarry Professional Environment/vocab/migrations/0010_vocabsection.py` with:

```python
import django.db.models.deletion
from django.db import migrations, models

SECTIONS = [
    ('essential-verbs', 'Essential Verbs', 'basic'),
    ('people-relationships', 'People & Relationships', 'basic'),
    ('mind-feelings', 'Mind & Feelings', 'basic'),
    ('home-daily-life', 'Home & Daily Life', 'basic'),
    ('the-natural-world', 'The Natural World', 'basic'),
    ('body-health', 'Body & Health', 'basic'),
    ('out-about', 'Out & About', 'basic'),
    ('time-description', 'Time & Description', 'basic'),
    ('numbers-learning', 'Numbers & Learning', 'basic'),
    ('sports-hobbies', 'Sports & Hobbies', 'basic'),
    ('emotions-in-depth', 'Emotions in Depth', 'intermediate'),
    ('personality-character', 'Personality & Character', 'intermediate'),
    ('mind-behaviour-psychology', 'Mind, Behaviour & Psychology', 'intermediate'),
    ('society-social-issues', 'Society & Social Issues', 'intermediate'),
    ('work-career', 'Work & Career', 'intermediate'),
    ('education-society', 'Education & Society', 'intermediate'),
    ('economics-finance', 'Economics & Finance', 'intermediate'),
    ('politics-global-affairs', 'Politics & Global Affairs', 'intermediate'),
    ('environment-climate', 'Environment & Climate', 'intermediate'),
    ('health-medicine', 'Health & Medicine', 'intermediate'),
    ('science-innovation', 'Science & Innovation', 'intermediate'),
    ('technology-media', 'Technology & Media', 'intermediate'),
    ('media-journalism', 'Media & Journalism', 'intermediate'),
    ('cities-urban-life', 'Cities & Urban Life', 'intermediate'),
    ('travel-culture-society', 'Travel, Culture & Society', 'intermediate'),
    ('food-nutrition-culture', 'Food, Nutrition & Culture', 'intermediate'),
    ('arts-media-culture', 'Arts, Media & Culture', 'intermediate'),
    ('language-communication', 'Language & Communication', 'intermediate'),
    ('action-process-verbs', 'Action & Process Verbs', 'intermediate'),
    ('quality-degree-adjectives', 'Quality & Degree Adjectives', 'intermediate'),
    ('idioms-collocations', 'Idioms & Collocations', 'intermediate'),
    ('connectors-discourse-markers', 'Connectors & Discourse Markers', 'intermediate'),
    ('academic-language-writing', 'Academic Language & Writing', 'intermediate'),
    ('verbs-for-writing-analysis', 'Verbs for Writing & Analysis', 'intermediate'),
    ('precision-control-vocabulary', 'Precision & Control Vocabulary', 'intermediate'),
    ('b2-noun-bank', 'B2 Noun Bank', 'intermediate'),
    ('b2-milestone-sets', 'B2 Milestone Sets', 'intermediate'),
    ('negative-qualities-criticism', 'Negative Qualities & Criticism', 'advanced'),
    ('positive-qualities-strength', 'Positive Qualities & Strength', 'advanced'),
    ('mind-emotion-description', 'Mind, Emotion & Description', 'advanced'),
    ('scale-change-society', 'Scale, Change & Society', 'advanced'),
    ('academic-writing-toolkit', 'Academic Writing Toolkit', 'advanced'),
    ('formal-english-fixed-expressions', 'Formal English & Fixed Expressions', 'advanced'),
    ('ielts-writing-themes-i', 'IELTS Writing Themes I', 'advanced'),
    ('ielts-writing-themes-ii', 'IELTS Writing Themes II', 'advanced'),
    ('academic-writing-toolkit-ii', 'Academic Writing Toolkit II', 'advanced'),
    ('vivid-description-communication', 'Vivid Description & Communication', 'advanced'),
    ('cognition-logic-research', 'Cognition, Logic & Research', 'advanced'),
    ('academic-connectors-iii', 'Academic Connectors III', 'advanced'),
    ('career-business-leadership', 'Career, Business & Leadership', 'advanced'),
    ('workplace-tasks-formal-language', 'Workplace Tasks & Formal Language', 'advanced'),
    ('governance-economy-society', 'Governance, Economy & Society', 'advanced'),
    ('personality-relationships-conflict', 'Personality, Relationships & Conflict', 'advanced'),
    ('everyday-life-money-idioms', 'Everyday Life, Money & Idioms', 'advanced'),
    ('science-tech-innovation', 'Science, Tech & Innovation', 'advanced'),
    ('nature-climate-energy', 'Nature, Climate & Energy', 'advanced'),
    ('travel-culture-urban-life', 'Travel, Culture & Urban Life', 'advanced'),
    ('lifestyle-leisure-wellbeing', 'Lifestyle, Leisure & Wellbeing', 'advanced'),
    ('storytelling-humour-persuasion', 'Storytelling, Humour & Persuasion', 'advanced'),
    ('description-size-sound-movement', 'Description: Size, Sound & Movement', 'advanced'),
    ('habits-comparison-politeness', 'Habits, Comparison & Politeness', 'advanced'),
    ('mind-abstract-thought', 'Mind & Abstract Thought', 'advanced'),
    ('society-rights-change', 'Society, Rights & Change', 'advanced'),
    ('global-power-economy', 'Global Power & Economy', 'advanced'),
    ('philosophy-critical-thought', 'Philosophy & Critical Thought', 'advanced'),
    ('arts-history-culture', 'Arts, History & Culture', 'advanced'),
    ('science-research-medicine', 'Science, Research & Medicine', 'advanced'),
    ('academic-register-style', 'Academic Register & Style', 'advanced'),
    ('precision-literary-language', 'Precision & Literary Language', 'advanced'),
    ('advanced-adjectives', 'Advanced Adjectives', 'advanced'),
    ('advanced-verbs-nouns', 'Advanced Verbs & Nouns', 'advanced'),
    ('formal-nouns-qualifiers', 'Formal Nouns & Qualifiers', 'advanced'),
    ('ielts-essay-mastery', 'IELTS Essay Mastery', 'advanced'),
    ('advanced-lexical-expansion', 'Advanced Lexical Expansion', 'advanced'),
    ('c2-finishing-sets', 'C2 Finishing Sets', 'advanced'),
]

CATEGORY_SECTIONS = {
    'neg-intensity': 'Negative Qualities & Criticism',
    'deception-falsehood': 'Negative Qualities & Criticism',
    'judgment-criticism': 'Negative Qualities & Criticism',
    'weakness-deterioration': 'Negative Qualities & Criticism',
    'approval-excellence': 'Positive Qualities & Strength',
    'strength-persistence': 'Positive Qualities & Strength',
    'support-agreement': 'Positive Qualities & Strength',
    'ethics-morality': 'Positive Qualities & Strength',
    'emotions-psych': 'Mind, Emotion & Description',
    'appearance-character': 'Mind, Emotion & Description',
    'tone-atmosphere': 'Mind, Emotion & Description',
    'thinking-intelligence': 'Mind, Emotion & Description',
    'scope-scale': 'Scale, Change & Society',
    'magnitude-impact': 'Scale, Change & Society',
    'change-transformation': 'Scale, Change & Society',
    'society-politics': 'Scale, Change & Society',
    'clarity-certainty': 'Academic Writing Toolkit',
    'academic-stance': 'Academic Writing Toolkit',
    'connectors-transitions': 'Academic Writing Toolkit',
    'linking-words': 'Academic Writing Toolkit',
    'professional-register': 'Formal English & Fixed Expressions',
    'abstract-nouns': 'Formal English & Fixed Expressions',
    'phrasal-verbs': 'Formal English & Fixed Expressions',
    'collocations': 'Formal English & Fixed Expressions',
    'trends-data': 'IELTS Writing Themes I',
    'opinion-argument': 'IELTS Writing Themes I',
    'education-learning': 'IELTS Writing Themes I',
    'work-career': 'IELTS Writing Themes I',
    'environment-sustainability': 'IELTS Writing Themes II',
    'technology-modern-life': 'IELTS Writing Themes II',
    'travel-society-culture': 'IELTS Writing Themes II',
    'health-lifestyle': 'IELTS Writing Themes II',
    'precision-upgrades': 'Mind, Emotion & Description',
    'essay-power-words': 'Academic Writing Toolkit',
    'society-mind-rhetoric': 'Scale, Change & Society',
    'hedging-likelihood': 'Academic Writing Toolkit II',
    'cause-consequence': 'Academic Writing Toolkit II',
    'connectors-time-sequence': 'Academic Writing Toolkit II',
    'difficulty-risk': 'Academic Writing Toolkit II',
    'proactive-action': 'Vivid Description & Communication',
    'quantity-degree': 'Vivid Description & Communication',
    'vivid-everyday': 'Vivid Description & Communication',
    'communication-disclosure': 'Vivid Description & Communication',
    'cognitive-verbs': 'Cognition, Logic & Research',
    'research-inquiry': 'Cognition, Logic & Research',
    'critical-reasoning': 'Cognition, Logic & Research',
    'memory-perception': 'Cognition, Logic & Research',
    'academic-connectors-iii': 'Academic Connectors III',
    'emphasis-contrast': 'Academic Connectors III',
    'cause-purpose': 'Academic Connectors III',
    'summary-conclusion': 'Academic Connectors III',
    'business-finance': 'Career, Business & Leadership',
    'workplace-communication': 'Career, Business & Leadership',
    'leadership-management': 'Career, Business & Leadership',
    'career-growth': 'Career, Business & Leadership',
    'work-tasks': 'Workplace Tasks & Formal Language',
    'general-useful-verbs': 'Workplace Tasks & Formal Language',
    'formal-register-ii': 'Workplace Tasks & Formal Language',
    'governance-law': 'Governance, Economy & Society',
    'economy-trade': 'Governance, Economy & Society',
    'social-justice': 'Governance, Economy & Society',
    'growth-expansion': 'Governance, Economy & Society',
    'personality-traits-ii': 'Personality, Relationships & Conflict',
    'interpersonal-relationships': 'Personality, Relationships & Conflict',
    'conflict-resolution': 'Personality, Relationships & Conflict',
    'decision-making': 'Personality, Relationships & Conflict',
    'everyday-idioms': 'Everyday Life, Money & Idioms',
    'money-shopping': 'Everyday Life, Money & Idioms',
    'food-health': 'Everyday Life, Money & Idioms',
    'tech-digital-life': 'Science, Tech & Innovation',
    'science-innovation': 'Science, Tech & Innovation',
    'digital-communication': 'Science, Tech & Innovation',
    'ai-automation': 'Science, Tech & Innovation',
    'climate-weather': 'Nature, Climate & Energy',
    'nature-wildlife': 'Nature, Climate & Energy',
    'energy-resources-ii': 'Nature, Climate & Energy',
    'travel-experiences': 'Travel, Culture & Urban Life',
    'cultural-diversity': 'Travel, Culture & Urban Life',
    'urban-development': 'Travel, Culture & Urban Life',
    'lifestyle-habits': 'Lifestyle, Leisure & Wellbeing',
    'leisure-hobbies': 'Lifestyle, Leisure & Wellbeing',
    'health-wellbeing-ii': 'Lifestyle, Leisure & Wellbeing',
    'motivation-ambition': 'Lifestyle, Leisure & Wellbeing',
    'storytelling-narrative': 'Storytelling, Humour & Persuasion',
    'humor-wit': 'Storytelling, Humour & Persuasion',
    'persuasion-rhetoric-ii': 'Storytelling, Humour & Persuasion',
    'size-shape': 'Description: Size, Sound & Movement',
    'sound-light': 'Description: Size, Sound & Movement',
    'movement-action': 'Description: Size, Sound & Movement',
    'comparison-contrast': 'Habits, Comparison & Politeness',
    'habits-routines': 'Habits, Comparison & Politeness',
    'risk-caution': 'Habits, Comparison & Politeness',
    'politeness-formality': 'Habits, Comparison & Politeness',
    'core-action-verbs': 'Essential Verbs',
    'everyday-verbs-ii': 'Essential Verbs',
    'movement-position-verbs': 'Essential Verbs',
    'communication-basic': 'People & Relationships',
    'family-people': 'People & Relationships',
    'describing-people-basic': 'People & Relationships',
    'feelings-emotions-basic': 'Mind & Feelings',
    'home-household': 'Home & Daily Life',
    'food-drink-basic': 'Home & Daily Life',
    'time-calendar': 'Time & Description',
    'weather-nature-basic': 'The Natural World',
    'body-health-basic': 'Body & Health',
    'places-transport-basic': 'Out & About',
    'numbers-school-basic': 'Numbers & Learning',
    'colours-shapes-basic': 'Numbers & Learning',
    'sports-hobbies-basic': 'Sports & Hobbies',
    'complex-emotions': 'Emotions in Depth',
    'personality-character-inter': 'Personality & Character',
    'social-issues-inter': 'Society & Social Issues',
    'work-career-inter': 'Work & Career',
    'environment-inter': 'Environment & Climate',
    'health-medicine-inter': 'Health & Medicine',
    'technology-media-inter': 'Technology & Media',
    'academic-language-inter': 'Academic Language & Writing',
    'food-culture-inter': 'Food, Nutrition & Culture',
    'travel-culture-inter': 'Travel, Culture & Society',
    'education-society-inter': 'Education & Society',
    'law-justice-inter': 'Society & Social Issues',
    'psychology-behaviour-inter': 'Mind, Behaviour & Psychology',
    'communication-language-inter': 'Language & Communication',
    'economics-finance-inter': 'Economics & Finance',
    'global-issues-inter': 'Politics & Global Affairs',
    'arts-culture-inter': 'Arts, Media & Culture',
    'science-discovery-inter': 'Science & Innovation',
    'urban-architecture-inter': 'Cities & Urban Life',
    'ethics-philosophy-inter': 'Society & Social Issues',
    'relationships-society-inter': 'Personality & Character',
    'media-journalism-inter': 'Media & Journalism',
    'health-lifestyle-inter': 'Health & Medicine',
    'abstract-thought-c1': 'Mind & Abstract Thought',
    'rhetoric-persuasion-c1': 'Storytelling, Humour & Persuasion',
    'advanced-vocab-c1': 'Precision & Literary Language',
    'social-change-c1': 'Society, Rights & Change',
    'human-nature-c1': 'Society, Rights & Change',
    'academic-c1-advanced': 'Academic Register & Style',
    'environment-c1': 'Nature, Climate & Energy',
    'globalisation-c1': 'Global Power & Economy',
    'power-politics-c1': 'Global Power & Economy',
    'cognition-mind-c1': 'Mind & Abstract Thought',
    'language-linguistics-c1': 'Academic Register & Style',
    'medicine-biology-c1': 'Science, Research & Medicine',
    'technology-future-c1': 'Science, Tech & Innovation',
    'history-civilisation-c1': 'Arts, History & Culture',
    'arts-expression-c1': 'Arts, History & Culture',
    'philosophy-thought-c2': 'Philosophy & Critical Thought',
    'advanced-adjectives-c2': 'Advanced Adjectives',
    'advanced-verbs-c2': 'Advanced Verbs & Nouns',
    'advanced-nouns-c2': 'Advanced Verbs & Nouns',
    'c2-expressions': 'C2 Finishing Sets',
    'emotions-b-extended': 'Emotions in Depth',
    'describing-actions-b': 'Action & Process Verbs',
    'work-society-b2-extended': 'Work & Career',
    'nature-landscape-b2': 'Environment & Climate',
    'language-communication-b2': 'Language & Communication',
    'politics-governance-b2': 'Politics & Global Affairs',
    'academic-style-c1b': 'Academic Register & Style',
    'ielts-writing-c1-ext': 'IELTS Essay Mastery',
    'science-tech-b2-ext': 'Science & Innovation',
    'health-body-b2-ext': 'Health & Medicine',
    'descriptive-adjectives-c1': 'Advanced Adjectives',
    'idioms-phrases-b2': 'Idioms & Collocations',
    'environment-sustainability-c1': 'Nature, Climate & Energy',
    'academic-verbs-c1': 'Academic Register & Style',
    'literary-descriptive-c2': 'Precision & Literary Language',
    'formal-nouns-c1b': 'Formal Nouns & Qualifiers',
    'arts-media-b2': 'Arts, Media & Culture',
    'philosophy-ethics-c1-ext': 'Philosophy & Critical Thought',
    'geography-demography-b2': 'Politics & Global Affairs',
    'business-economics-c1': 'Career, Business & Leadership',
    'social-human-rights-c1': 'Society, Rights & Change',
    'verbs-precise-b2': 'Action & Process Verbs',
    'cognition-learning-c1': 'Mind, Behaviour & Psychology',
    'idioms-c1-complex': 'Idioms & Collocations',
    'c2-precision-words': 'Precision & Literary Language',
    'crime-justice-c1': 'Governance, Economy & Society',
    'personality-adjectives-c1': 'Advanced Adjectives',
    'academic-nouns-b2': 'Academic Language & Writing',
    'verbs-b2-advanced': 'Verbs for Writing & Analysis',
    'complex-sentence-connectors': 'Connectors & Discourse Markers',
    'collocations-formal-c1': 'Academic Language & Writing',
    'global-issues-c1b': 'Global Power & Economy',
    'word-formation-b2': 'Language & Communication',
    'common-adjectives-b1b': 'Quality & Degree Adjectives',
    'mind-emotion-c1-ext': 'Mind & Abstract Thought',
    'education-learning-b2': 'Education & Society',
    'housing-urban-b2': 'Cities & Urban Life',
    'c2-final-vocab': 'C2 Finishing Sets',
    'technology-digital-b2': 'Technology & Media',
    'food-culture-ext': 'Food, Nutrition & Culture',
    'travel-tourism-b2': 'Travel, Culture & Society',
    'advanced-connectors-c1-final': 'Academic Connectors III',
    'social-media-comm-b2': 'Media & Journalism',
    'science-research-c1': 'Science, Research & Medicine',
    'abstract-concepts-c1-final': 'Philosophy & Critical Thought',
    'common-verbs-b1-ext': 'Action & Process Verbs',
    'formal-adverbs-c1-ext': 'Formal Nouns & Qualifiers',
    'complex-nouns-b2-final': 'B2 Noun Bank',
    'adjectives-b2-quality': 'Quality & Degree Adjectives',
    'final-nouns-c1': 'Formal Nouns & Qualifiers',
    'core-ielts-vocab-final': 'B2 Milestone Sets',
    'final-advanced-b2': 'B2 Milestone Sets',
    'key-transitions-b2-final': 'Connectors & Discourse Markers',
    'additional-b2-vocab': 'B2 Milestone Sets',
    'ielts-essay-vocab': 'IELTS Essay Mastery',
    'b2-nouns-final-set': 'B2 Noun Bank',
    'c1-writing-toolkit': 'IELTS Essay Mastery',
    'final-20-words': 'C2 Finishing Sets',
    'a1plus-body-health': 'Body & Health',
    'a1plus-food-drink': 'Home & Daily Life',
    'a1plus-home-objects': 'Home & Daily Life',
    'a1plus-adjectives-basic': 'Time & Description',
    'a1plus-everyday-verbs': 'Essential Verbs',
    'a1plus-clothes-appearance': 'Home & Daily Life',
    'a1plus-places-transport': 'Out & About',
    'a1plus-school-classroom': 'Numbers & Learning',
    'a1plus-weather-nature': 'The Natural World',
    'a1plus-shopping-money': 'Out & About',
    'a1plus-time-routines': 'Time & Description',
    'a2plus-feelings-opinions': 'Mind & Feelings',
    'a2plus-descriptive-adjectives': 'Time & Description',
    'a2plus-everyday-verbs': 'Essential Verbs',
    'a2plus-travel-places': 'Travel, Culture & Society',
    'a2plus-work-education': 'Work & Career',
    'a2plus-entertainment': 'Sports & Hobbies',
    'b1plus-opinion-discussion': 'Academic Language & Writing',
    'b1plus-society-community': 'Society & Social Issues',
    'b1plus-environment': 'Environment & Climate',
    'b1plus-health-lifestyle': 'Health & Medicine',
    'b1plus-personality': 'Personality & Character',
    'b1plus-technology-media': 'Technology & Media',
    'b1plus-education-study': 'Education & Society',
    'b1plus-economy-work': 'Economics & Finance',
    'c1plus-formal-verbs': 'Formal English & Fixed Expressions',
    'c1plus-adjectives-advanced': 'Mind, Emotion & Description',
    'c1plus-abstract-nouns': 'Formal English & Fixed Expressions',
    'c1plus-literary-expressive': 'Mind, Emotion & Description',
    'c1plus-academic-discourse': 'Academic Writing Toolkit',
    'b2plus-analysis-verbs': 'Verbs for Writing & Analysis',
    'b2plus-nuanced-adjectives': 'Quality & Degree Adjectives',
    'c2plus-rare-adjectives': 'Advanced Lexical Expansion',
    'c2plus-elevated-verbs': 'Advanced Lexical Expansion',
    'c2plus-abstract-nouns-ii': 'Advanced Lexical Expansion',
    'c2plus-idioms-collocations': 'Advanced Lexical Expansion',
    'b2plus-precision-adjectives': 'Precision & Control Vocabulary',
    'b2plus-control-verbs': 'Precision & Control Vocabulary',
    'a2-everyday-essentials': 'Home & Daily Life',
    'c1plus-bias-power-hardship': 'Society, Rights & Change',
}


def seed_and_backfill(apps, schema_editor):
    VocabSection = apps.get_model('vocab', 'VocabSection')
    Category = apps.get_model('vocab', 'Category')

    sections_by_name = {}
    for order, (slug, name, tier) in enumerate(SECTIONS):
        section = VocabSection.objects.create(slug=slug, name=name, tier=tier, order=order)
        sections_by_name[name] = section

    for category in Category.objects.all():
        section_name = CATEGORY_SECTIONS.get(category.slug)
        section = sections_by_name.get(section_name) if section_name else None
        if section:
            category.section = section
            category.save(update_fields=['section'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0009_grammarsection'),
    ]

    operations = [
        migrations.CreateModel(
            name='VocabSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('tier', models.CharField(choices=[('basic', 'Basic'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], max_length=12)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='category',
            name='section',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='categories', to='vocab.vocabsection',
            ),
        ),
        migrations.RunPython(seed_and_backfill, reverse_code=noop),
    ]
```

Note: the 75 slugs are already pre-computed and hardcoded into `SECTIONS` as verified literal values (matching exactly how `GrammarSection`'s own migration hardcodes its slugs rather than computing them at migration time) — no `slugify()` call is needed in the migration itself.

- [ ] **Step 3: Apply the migration and verify manually**

Run (from `VocabLarry Professional Environment/`): `python manage.py migrate vocab`

Then verify via `python manage.py shell`:

```python
from vocab.models import VocabSection, Category
assert VocabSection.objects.count() == 75
assert VocabSection.objects.filter(tier='basic').count() == 10
assert VocabSection.objects.filter(tier='intermediate').count() == 27
assert VocabSection.objects.filter(tier='advanced').count() == 38
assert Category.objects.filter(section__isnull=True).count() == 0, "every category must have a section"
# Spot-check across all three tiers
assert Category.objects.get(slug='core-action-verbs').section.name == 'Essential Verbs'
assert Category.objects.get(slug='complex-emotions').section.name == 'Emotions in Depth'
assert Category.objects.get(slug='neg-intensity').section.name == 'Negative Qualities & Criticism'
essential_verbs = VocabSection.objects.get(name='Essential Verbs')
assert essential_verbs.categories.count() == 5
```

Expected: all assertions pass silently (no output = success; any `AssertionError` means the migration data has a mistake to fix before proceeding).

- [ ] **Step 4: Commit**

```bash
git add "VocabLarry Professional Environment/vocab/models.py" "VocabLarry Professional Environment/vocab/migrations/0010_vocabsection.py"
git commit -m "feat(vlpe): add VocabSection model and migrate the 75-section/250-category grouping"
```

---

### Task 2: Relocate shared CSS to base.css, rename the accordion-toggle script

**Files:**
- Modify: `VocabLarry Professional Environment/static/css/grammar.css` (remove the two relocated blocks)
- Modify: `VocabLarry Professional Environment/static/css/base.css` (add the two relocated blocks)
- Rename: `VocabLarry Professional Environment/static/js/grammar-browse.js` → `VocabLarry Professional Environment/static/js/section-accordion.js`
- Modify: `VocabLarry Professional Environment/templates/grammar/browse.html` (update the script `src` reference)

**Interfaces:**
- Consumes: nothing new.
- Produces: `.section-block`/`.section-block-*` and `.cat-view-title-row`/`.cat-view-icon`/`.cat-view-name`/`.cat-view-sub` now live in `base.css`, available to any template that loads it (all of them do, via `base.html`) without needing `grammar.css` specifically. `static/js/section-accordion.js` — Task 3's template loads this filename.
- This task changes no markup and no JS logic (byte-identical file content, just relocated/renamed), so no existing test's assertions change. Verified by the full existing suite staying green — specifically by Grammar Browse's own tests, which exercise this exact CSS/JS without any changes.

- [ ] **Step 1: Remove `.section-block` and `.cat-view-*` from grammar.css**

In `VocabLarry Professional Environment/static/css/grammar.css`, delete these two blocks entirely (including their header comments):

```css
/* Section accordion — ported from production's .section-block family */
.section-block{
  margin-bottom: 12px; border: 1px solid var(--border); border-radius: 22px; overflow: hidden;
  background: var(--card-bg);
  transition: border-color .35s var(--ease-luxe), box-shadow .35s var(--ease-luxe), transform .35s var(--ease-luxe);
}
.section-block:hover{ border-color: rgb(var(--violet) / .35); box-shadow: 0 18px 44px rgba(0,0,0,.14); transform: translateY(-1px); }
.section-block.open{ border-color: rgb(var(--violet) / .4); box-shadow: 0 22px 56px rgba(0,0,0,.16); }
.section-block-header{ display: flex; align-items: center; gap: 18px; padding: 20px 26px; cursor: pointer; user-select: none; }
.section-block-num{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-weight: 800; font-size: 2.1rem;
  letter-spacing: -.05em; line-height: 1; color: var(--text); opacity: .14; min-width: 54px;
  transition: opacity .35s var(--ease-luxe), color .35s var(--ease-luxe);
}
.section-block:hover .section-block-num, .section-block.open .section-block-num{ opacity: .85; color: rgb(var(--violet)); }
.section-block-info{ flex: 1; min-width: 0; }
.section-block-name{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-size: 1.05rem; font-weight: 800;
  color: var(--text); margin-bottom: 3px; line-height: 1.2; letter-spacing: -.01em;
}
.section-block-meta{ font-size: .85rem; color: var(--muted); font-family: var(--serif); font-style: italic; }
.section-block-right{ display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.section-block-prog{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.section-block-pbar{ width: 72px; height: 2px; border-radius: 99px; background: rgb(var(--violet) / .12); overflow: hidden; }
.section-block-pfill{ height: 100%; border-radius: 99px; background: rgb(var(--violet)); transition: width .4s ease; }
.section-block-pct{ font-size: .72rem; font-weight: 700; color: rgb(var(--violet)); font-family: 'JetBrains Mono',monospace; }
.section-block-chevron{
  font-size: 1.1rem; color: var(--muted); opacity: .6;
  transition: transform .3s cubic-bezier(.25,.46,.45,.94), opacity .2s ease;
}
.section-block.open .section-block-chevron{ transform: rotate(90deg); opacity: 1; color: rgb(var(--violet)); }
.section-block-divider{ height: 1px; background: rgb(var(--violet) / .12); margin: 0 20px; display: none; }
.section-block.open .section-block-divider{ display: block; }
.section-block-body{ max-height: 0; overflow: hidden; transition: max-height .4s cubic-bezier(.25,.46,.45,.94); }
.section-block-body-inner{ padding: 18px 18px 20px; }
```

and:

```css
/* Topic detail header — ported from production's .cat-view-* family */
.cat-view-title-row{ display: flex; align-items: center; gap: 14px; }
.cat-view-icon{
  width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center;
  justify-content: center; font-size: 1.5rem; flex-shrink: 0; background: var(--card-bg);
  border: 2px solid var(--accent-c, rgb(var(--violet))); color: var(--accent-c, rgb(var(--violet)));
}
.cat-view-name{ font-size: 1.65rem; font-weight: 800; font-family: 'Plus Jakarta Sans','Sora',sans-serif; margin: 0; color: var(--accent-c, rgb(var(--violet))); }
.cat-view-sub{ font-size: .9rem; color: var(--muted); margin-top: 3px; }
```

- [ ] **Step 2: Add both blocks to base.css**

Append both blocks (exactly as shown in Step 1, unchanged) to the end of `VocabLarry Professional Environment/static/css/base.css`, with an updated header comment noting the shared status:

```css

/* Section accordion — ported from production's .section-block family.
   Shared by Grammar Browse and Vocabulary Category Browse (originally
   built for Grammar only; relocated here once Vocab needed the
   identical component). */
.section-block{
  margin-bottom: 12px; border: 1px solid var(--border); border-radius: 22px; overflow: hidden;
  background: var(--card-bg);
  transition: border-color .35s var(--ease-luxe), box-shadow .35s var(--ease-luxe), transform .35s var(--ease-luxe);
}
.section-block:hover{ border-color: rgb(var(--violet) / .35); box-shadow: 0 18px 44px rgba(0,0,0,.14); transform: translateY(-1px); }
.section-block.open{ border-color: rgb(var(--violet) / .4); box-shadow: 0 22px 56px rgba(0,0,0,.16); }
.section-block-header{ display: flex; align-items: center; gap: 18px; padding: 20px 26px; cursor: pointer; user-select: none; }
.section-block-num{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-weight: 800; font-size: 2.1rem;
  letter-spacing: -.05em; line-height: 1; color: var(--text); opacity: .14; min-width: 54px;
  transition: opacity .35s var(--ease-luxe), color .35s var(--ease-luxe);
}
.section-block:hover .section-block-num, .section-block.open .section-block-num{ opacity: .85; color: rgb(var(--violet)); }
.section-block-info{ flex: 1; min-width: 0; }
.section-block-name{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-size: 1.05rem; font-weight: 800;
  color: var(--text); margin-bottom: 3px; line-height: 1.2; letter-spacing: -.01em;
}
.section-block-meta{ font-size: .85rem; color: var(--muted); font-family: var(--serif); font-style: italic; }
.section-block-right{ display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.section-block-prog{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.section-block-pbar{ width: 72px; height: 2px; border-radius: 99px; background: rgb(var(--violet) / .12); overflow: hidden; }
.section-block-pfill{ height: 100%; border-radius: 99px; background: rgb(var(--violet)); transition: width .4s ease; }
.section-block-pct{ font-size: .72rem; font-weight: 700; color: rgb(var(--violet)); font-family: 'JetBrains Mono',monospace; }
.section-block-chevron{
  font-size: 1.1rem; color: var(--muted); opacity: .6;
  transition: transform .3s cubic-bezier(.25,.46,.45,.94), opacity .2s ease;
}
.section-block.open .section-block-chevron{ transform: rotate(90deg); opacity: 1; color: rgb(var(--violet)); }
.section-block-divider{ height: 1px; background: rgb(var(--violet) / .12); margin: 0 20px; display: none; }
.section-block.open .section-block-divider{ display: block; }
.section-block-body{ max-height: 0; overflow: hidden; transition: max-height .4s cubic-bezier(.25,.46,.45,.94); }
.section-block-body-inner{ padding: 18px 18px 20px; }

/* Category/topic detail header — ported from production's .cat-view-*
   family. Shared by Grammar Topic Detail and the Vocabulary category
   word-list drill-in page. */
.cat-view-title-row{ display: flex; align-items: center; gap: 14px; }
.cat-view-icon{
  width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center;
  justify-content: center; font-size: 1.5rem; flex-shrink: 0; background: var(--card-bg);
  border: 2px solid var(--accent-c, rgb(var(--violet))); color: var(--accent-c, rgb(var(--violet)));
}
.cat-view-name{ font-size: 1.65rem; font-weight: 800; font-family: 'Plus Jakarta Sans','Sora',sans-serif; margin: 0; color: var(--accent-c, rgb(var(--violet))); }
.cat-view-sub{ font-size: .9rem; color: var(--muted); margin-top: 3px; }
```

- [ ] **Step 3: Rename the accordion-toggle script and update its reference**

Rename `VocabLarry Professional Environment/static/js/grammar-browse.js` to `VocabLarry Professional Environment/static/js/section-accordion.js` — file content unchanged (it already has zero Grammar-specific logic, operating purely on `.section-block` class selectors):

```bash
git mv "VocabLarry Professional Environment/static/js/grammar-browse.js" "VocabLarry Professional Environment/static/js/section-accordion.js"
```

In `VocabLarry Professional Environment/templates/grammar/browse.html`, find the script tag referencing the old filename and update it:

```html
<script src="{% static 'js/grammar-browse.js' %}" defer></script>
```

becomes:

```html
<script src="{% static 'js/section-accordion.js' %}" defer></script>
```

- [ ] **Step 4: Run the full test suite to confirm no regressions**

Run (from `VocabLarry Professional Environment/`): `pytest`
Expected: all existing tests pass unchanged — this task altered no markup, no JS behavior, and no test-visible content, only file locations.

- [ ] **Step 5: Manual verification that Grammar Browse still renders identically**

Using a browser, navigate to `/grammar/category/` and confirm: section accordions still expand/collapse on click exactly as before, `.cat-view-*` header still renders correctly on a Grammar Topic Detail page (`/grammar/category/<any-topic-slug>/`). This is a pure relocation, so nothing should look different — the point of this check is confirming the relocation didn't silently break the load order or introduce a CSS specificity conflict with anything already in `base.css`.

- [ ] **Step 6: Commit**

```bash
git add "VocabLarry Professional Environment/static/css/base.css" "VocabLarry Professional Environment/static/css/grammar.css" "VocabLarry Professional Environment/static/js/section-accordion.js" "VocabLarry Professional Environment/templates/grammar/browse.html"
git commit -m "refactor(vlpe): relocate .section-block/.cat-view-* CSS to base.css and rename grammar-browse.js to section-accordion.js as shared infrastructure"
```

---

### Task 3: Vocabulary Category browse page — section accordions, Tier filter, pagination

**Files:**
- Modify: `VocabLarry Professional Environment/config/views_vocab.py` (rewrite `vocab_browse`, add `import itertools`)
- Modify: `VocabLarry Professional Environment/templates/vocab/browse.html` (full-file rewrite)
- Modify: `VocabLarry Professional Environment/tests/test_vocab_pages.py` (replace/add tests)

**Interfaces:**
- Consumes: `VocabSection`/`Category.section` from Task 1. `.section-block` family and `section-accordion.js` from Task 2. Pre-existing `_pagination_window` helper, `.filters`/`.chip`/`.search-row`/`.filter-row`/`.clear-btn`/`.cat-grid`/`.cat-card`/`.cefr-badge`/`.pagination`/`.page-btn`/`.page-ellipsis` CSS, `category_icon` template filter.
- Produces: no new interfaces consumed by other tasks — Task 4 is independent of this task's internals (it only needs `Category.section`, already produced by Task 1).

- [ ] **Step 1: Replace the existing tests and add new ones**

In `VocabLarry Professional Environment/tests/test_vocab_pages.py`, the existing category-browse tests assume a flat, unpaginated category list with no section grouping. Replace these three:

```python
@pytest.mark.django_db
def test_vocabulary_category_list_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/category/')
    assert r.status_code == 200
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_search_filters_by_name(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/category/', {'q': 'anim'})
    html = r.content.decode()
    assert 'Animals' in html and 'Food' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_cefr_filter(cefr_a1, cefr_b1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_b1)
    c = Client()
    r = c.get('/vocabulary/category/', {'cefr': 'A1'})
    html = r.content.decode()
    assert 'Animals' in html and 'Food' not in html
```

with (these create their own `VocabSection` fixture rows, matching this project's `--no-migrations` convention):

```python
@pytest.fixture
def vocab_sections(db):
    from vocab.models import VocabSection
    basic = VocabSection.objects.create(slug='essential-verbs', name='Essential Verbs', tier='basic', order=0)
    inter = VocabSection.objects.create(slug='emotions-in-depth', name='Emotions in Depth', tier='intermediate', order=10)
    adv = VocabSection.objects.create(slug='negative-qualities-criticism', name='Negative Qualities & Criticism', tier='advanced', order=37)
    return {'basic': basic, 'intermediate': inter, 'advanced': adv}


@pytest.mark.django_db
def test_vocabulary_category_list_shows_section_accordions(cefr_a1, vocab_sections):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=vocab_sections['basic'])
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'class="section-block-name">Essential Verbs<' in html
    assert 'class="section-block"' in html
    assert 'Animals' in html


@pytest.mark.django_db
def test_vocabulary_category_list_search_filters_within_sections(cefr_a1, vocab_sections):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=vocab_sections['basic'])
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1, section=vocab_sections['basic'])
    c = Client()
    r = c.get('/vocabulary/category/', {'q': 'anim'})
    html = r.content.decode()
    assert 'Animals' in html and 'Food' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_cefr_filter(cefr_a1, cefr_b1, vocab_sections):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=vocab_sections['basic'])
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_b1, section=vocab_sections['basic'])
    c = Client()
    r = c.get('/vocabulary/category/', {'cefr': 'A1'})
    html = r.content.decode()
    assert 'Animals' in html and 'Food' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_section_with_no_matches_is_hidden(cefr_a1, cefr_b1, vocab_sections):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=vocab_sections['basic'])
    Category.objects.create(slug='ethics', name='Ethics', order=1, cefr_level=cefr_b1, section=vocab_sections['advanced'])
    c = Client()
    r = c.get('/vocabulary/category/', {'cefr': 'A1'})
    html = r.content.decode()
    assert 'Essential Verbs' in html
    assert 'Negative Qualities' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_tier_filter(cefr_a1, vocab_sections):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=vocab_sections['basic'])
    Category.objects.create(slug='ethics', name='Ethics', order=1, cefr_level=cefr_a1, section=vocab_sections['advanced'])
    c = Client()
    r = c.get('/vocabulary/category/', {'tier': 'basic'})
    html = r.content.decode()
    assert 'Essential Verbs' in html
    assert 'Negative Qualities' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_pagination(cefr_a1):
    from vocab.models import VocabSection
    for i in range(12):
        section = VocabSection.objects.create(slug=f'section-{i}', name=f'Section {i}', tier='basic', order=i)
        Category.objects.create(slug=f'cat-{i}', name=f'Category {i}', order=i, cefr_level=cefr_a1, section=section)
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert html.count('class="section-block"') == 10
    assert 'class="pagination"' in html

    r2 = c.get('/vocabulary/category/', {'page': 2})
    html2 = r2.content.decode()
    assert html2.count('class="section-block"') == 2


@pytest.mark.django_db
def test_vocabulary_category_list_section_progress_shown_for_authenticated_only(cefr_a1, vocab_sections, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=vocab_sections['basic'])
    from vocab.models import Word
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {}
    regular_user.save(update_fields=['learn_map'])
    c = Client()

    r = c.get('/vocabulary/category/')
    assert 'section-block-pct' not in r.content.decode()

    c.force_login(regular_user)
    r2 = c.get('/vocabulary/category/')
    assert 'section-block-pct' in r2.content.decode()
```

- [ ] **Step 2: Run the new/changed tests to verify they fail**

Run: `pytest tests/test_vocab_pages.py -k "vocabulary_category_list" -v`
Expected: FAIL — the current view has no section grouping, no pagination, and `Category` has no `section` field usage yet in this view.

- [ ] **Step 3: Rewrite the `vocab_browse` view**

In `VocabLarry Professional Environment/config/views_vocab.py`, add `import itertools` as the first line of the file (before the existing `from collections import Counter`).

Replace the entire `vocab_browse` function with:

```python
def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()
    tier_filter = request.GET.get('tier', '').strip()

    categories = Category.objects.select_related('cefr_level', 'color', 'section').order_by('section__order', 'order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    categories = list(categories)

    word_category = dict(
        Word.objects.filter(category_id__in=[c.id for c in categories]).values_list('id', 'category_id')
    )
    word_counts = Counter(word_category.values())

    for category in categories:
        category.word_count = word_counts[category.id]

    if request.user.is_authenticated:
        learn_map = request.user.learn_map
        progress_by_category = {}
        for word_id_str, state in learn_map.items():
            try:
                word_id = int(word_id_str)
            except (TypeError, ValueError):
                continue
            category_id = word_category.get(word_id)
            if category_id is None:
                continue
            bucket = progress_by_category.setdefault(category_id, {'learned': 0, 'little': 0})
            if state == 'learned':
                bucket['learned'] += 1
            elif state == 'little':
                bucket['little'] += 1

        for category in categories:
            total = category.word_count
            bucket = progress_by_category.get(category.id, {'learned': 0, 'little': 0})
            learned = bucket['learned']
            little = bucket['little']
            category.progress = {
                'learned': learned,
                'little': little,
                'total': total,
                'learned_pct': round(learned / total * 100) if total else 0,
                'little_pct': round(little / total * 100) if total else 0,
                'complete': total > 0 and learned == total,
            }

        if progress_filter == 'learned':
            categories = [c for c in categories if c.progress['complete']]
        elif progress_filter == 'in_progress':
            categories = [
                c for c in categories
                if not c.progress['complete'] and (c.progress['learned'] or c.progress['little'])
            ]
        elif progress_filter == 'not_started':
            categories = [
                c for c in categories
                if not c.progress['learned'] and not c.progress['little']
            ]
    else:
        for category in categories:
            category.progress = None

    sections = []
    for section_id, group in itertools.groupby(categories, key=lambda c: c.section_id):
        if section_id is None:
            continue
        group = list(group)
        section = group[0].section
        if tier_filter and section.tier != tier_filter:
            continue
        total_words = sum(c.word_count for c in group)
        entry = {'section': section, 'categories': group, 'word_count': total_words}
        if request.user.is_authenticated:
            learned_total = sum(c.progress['learned'] for c in group)
            entry['progress_pct'] = round(learned_total / total_words * 100) if total_words else 0
        else:
            entry['progress_pct'] = None
        sections.append(entry)

    paginator = Paginator(sections, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'page_obj': page_obj,
        'pagination_window': _pagination_window(page_obj.number, paginator.num_pages),
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
        'progress_filter': progress_filter,
        'tier_filter': tier_filter,
    })
```

- [ ] **Step 4: Rewrite browse.html**

Replace the entire content of `VocabLarry Professional Environment/templates/vocab/browse.html` with:

```html
{% extends "base.html" %}
{% load static vocab_extras %}
{% block title %}Vocabulary — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-browse">
  <h1>Vocabulary</h1>
  <div class="mobile-page-switcher">
    <a class="chip active" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <div class="filters">
    <form method="get" class="search-row">
      <input type="search" name="q" value="{{ query }}" placeholder="Search categories…" data-i18n-placeholder="vocab.searchCategories">
      {% if cefr_filter %}<input type="hidden" name="cefr" value="{{ cefr_filter }}">{% endif %}
      {% if progress_filter %}<input type="hidden" name="progress" value="{{ progress_filter }}">{% endif %}
      {% if tier_filter %}<input type="hidden" name="tier" value="{{ tier_filter }}">{% endif %}
      <button type="submit" class="btn">Filter</button>
    </form>
    <div class="filter-row">
      <span class="filter-label">Tier</span>
      <a class="chip{% if not tier_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}">All</a>
      <a class="chip{% if tier_filter == 'basic' %} active{% endif %}" href="?q={{ query|urlencode }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&tier=basic">Basic</a>
      <a class="chip{% if tier_filter == 'intermediate' %} active{% endif %}" href="?q={{ query|urlencode }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&tier=intermediate">Intermediate</a>
      <a class="chip{% if tier_filter == 'advanced' %} active{% endif %}" href="?q={{ query|urlencode }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&tier=advanced">Advanced</a>
    </div>
    <div class="filter-row">
      <span class="filter-label" data-i18n="common.cefrLevel">CEFR Level</span>
      <a class="chip{% if not cefr_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}" data-i18n="common.all">All</a>
      {% for level in cefr_levels %}
      <a class="chip{% if cefr_filter == level.code %} active{% endif %}" data-browse-cefr="{{ level.code }}" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&cefr={{ level.code }}">{{ level.code }}</a>
      {% endfor %}
    </div>
    {% if user.is_authenticated %}
    <div class="filter-row">
      <span class="filter-label" data-i18n="common.progress">Progress</span>
      <a class="chip{% if not progress_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}" data-i18n="common.all">All</a>
      <a class="chip{% if progress_filter == 'learned' %} active{% endif %}" data-browse-status="completed" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=learned" data-i18n="common.completed">Completed</a>
      <a class="chip{% if progress_filter == 'in_progress' %} active{% endif %}" data-browse-status="inProgress" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=in_progress" data-i18n="common.inProgress">In Progress</a>
      <a class="chip{% if progress_filter == 'not_started' %} active{% endif %}" data-browse-status="notStarted" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=not_started" data-i18n="common.notStarted">Not Started</a>
    </div>
    {% endif %}
    <div class="filter-row" style="justify-content:flex-end;">
      <a class="clear-btn" href="{% url 'vocabulary_category_list' %}" data-i18n="common.clearFilters">Clear filters</a>
    </div>
  </div>

  {% if page_obj %}
  {% for entry in page_obj %}
  <div class="section-block">
    <div class="section-block-header">
      <div class="section-block-num">{{ entry.section.order|add:1|stringformat:"02d" }}</div>
      <div class="section-block-info">
        <div class="section-block-name">{{ entry.section.name }}</div>
        <div class="section-block-meta">{{ entry.categories|length }} categor{{ entry.categories|length|pluralize:"y,ies" }} · {{ entry.word_count }} words</div>
      </div>
      <div class="section-block-right">
        {% if entry.progress_pct is not None %}
        <div class="section-block-prog">
          <div class="section-block-pbar"><div class="section-block-pfill" style="width:{{ entry.progress_pct }}%"></div></div>
          <div class="section-block-pct">{{ entry.progress_pct }}%</div>
        </div>
        {% endif %}
        <span class="section-block-chevron">›</span>
      </div>
    </div>
    <div class="section-block-divider"></div>
    <div class="section-block-body">
      <div class="section-block-body-inner">
        <div class="cat-grid">
          {% for category in entry.categories %}
          <a class="cat-card" href="{% url 'vocabulary_category_detail' category.slug %}"
             style="--accent-c:{{ category.color.bg_hex|default:'#7c3aed' }};">
            <div class="cat-card-top">
              <span class="cat-tag"><svg class="ico" aria-hidden="true"><use href="#{{ category.icon|category_icon }}"/></svg> {{ category.word_count }} words</span>
              {% if category.cefr_level %}<span class="cefr-badge {{ category.cefr_level.code }}">{{ category.cefr_level.code }}</span>{% endif %}
              <svg class="ico cat-arrow" aria-hidden="true"><use href="#i-arrow-up-right"/></svg>
            </div>
            <div class="cat-name">{{ category.name }}</div>
            {% if category.progress %}
            <div class="cat-pbar-row">
              <div class="cat-pbar">
                <div class="cat-pfill-little" style="width:{{ category.progress.little_pct }}%"></div>
                <div class="cat-pfill" style="width:{{ category.progress.learned_pct }}%;{% if category.progress.complete %}background:#10b981;{% endif %}position:absolute;top:0;left:0;"></div>
              </div>
              {% if category.progress.complete %}
              <svg class="ico cat-medal" aria-hidden="true"><use href="#i-medal"/></svg>
              {% else %}
              <span class="cat-plabel">{{ category.progress.learned }}/{{ category.progress.total }}</span>
              {% endif %}
            </div>
            {% endif %}
          </a>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
  {% endfor %}
  {% if page_obj.paginator.num_pages > 1 %}
  <nav class="pagination">
    <a class="page-btn{% if not page_obj.has_previous %} disabled{% endif %}"
       href="{% if page_obj.has_previous %}?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&page={{ page_obj.previous_page_number }}{% else %}#{% endif %}">«</a>
    {% for p in pagination_window %}
      {% if p is None %}<span class="page-ellipsis">…</span>
      {% else %}<a class="page-btn{% if p == page_obj.number %} active{% endif %}" href="?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&page={{ p }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
    <a class="page-btn{% if not page_obj.has_next %} disabled{% endif %}"
       href="{% if page_obj.has_next %}?q={{ query|urlencode }}{% if tier_filter %}&tier={{ tier_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&page={{ page_obj.next_page_number }}{% else %}#{% endif %}">»</a>
  </nav>
  {% endif %}
  {% else %}
  <p class="vocab-empty">No categories match your search.</p>
  {% endif %}
</section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/section-accordion.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests/test_vocab_pages.py -k "vocabulary_category_list" -v`
Expected: PASS.

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass.

- [ ] **Step 7: Manual/Playwright verification**

This step cannot be verified by the Python test suite (accordion open/close visual behavior, real pagination at scale). Using a browser with the real ~5000-word/250-category dataset:
- Navigate to `/vocabulary/category/` — confirm 10 section accordions render, collapsed by default.
- Click a section header — confirm it expands to reveal that section's own category cards, with a working chevron rotation and smooth height transition (reusing the unmodified `section-accordion.js`).
- Click the Basic/Intermediate/Advanced tier chips — confirm the section list narrows to only that tier, and pagination adjusts accordingly (e.g. Basic's 10 sections should fit on one page with no pagination nav shown).
- Combine a CEFR filter with a search term — confirm sections with zero matching categories disappear entirely.
- As an authenticated user with some real progress, confirm each section's progress bar/percentage reflects the aggregate of its own categories only (spot-check one section's number by hand).
- Confirm both dark (default) and light theme render the section accordions and cat-cards correctly.

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry Professional Environment/config/views_vocab.py" "VocabLarry Professional Environment/templates/vocab/browse.html" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "feat(vlpe): add section-accordion grouping, Tier filter, and pagination to the Vocabulary Category browse page"
```

---

### Task 4: Category word-list (drill-in) page — section-aware header

**Files:**
- Modify: `VocabLarry Professional Environment/templates/vocab/category_word_list.html`
- Modify: `VocabLarry Professional Environment/tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: `Category.section` from Task 1. `.cat-view-title-row`/`.cat-view-icon`/`.cat-view-name`/`.cat-view-sub` from Task 2 (already relocated to `base.css`, available here without any new CSS). Pre-existing `category_icon` filter, `all_word_ids` context variable (already computed by the existing `vocab_category` view for bulk actions — reused here for the word-count meta text, no view change needed).
- Produces: no new interfaces consumed elsewhere — this is the final piece of this sub-project.

- [ ] **Step 1: Write the failing tests**

Add to `VocabLarry Professional Environment/tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocabulary_category_detail_shows_section_header(cefr_a1):
    from vocab.models import VocabSection
    section = VocabSection.objects.create(slug='essential-verbs', name='Essential Verbs', tier='basic', order=0)
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1, section=section)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'class="back-btn" href="/vocabulary/category/"' in html
    assert '← All Sections' in html
    assert 'class="cat-view-name">Animals<' in html
    assert '1 words · Essential Verbs' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_header_without_section(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'class="cat-view-name">Animals<' in html
    assert '1 words' in html
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_vocab_pages.py -k "vocabulary_category_detail_shows_section_header or vocabulary_category_detail_header_without_section" -v`
Expected: FAIL — the current template has no `.cat-view-*`/`.back-btn` header at all.

- [ ] **Step 3: Rewrite the header in category_word_list.html**

In `VocabLarry Professional Environment/templates/vocab/category_word_list.html`, replace:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{{ category.name }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-category">
  <p class="vocab-breadcrumb"><a href="{% url 'vocabulary_category_list' %}">Vocabulary</a> / {{ category.name }}</p>
  <h1>{{ category.name }}</h1>
  <div class="card-grid">
```

with:

```html
{% extends "base.html" %}
{% load static vocab_extras %}
{% block title %}{{ category.name }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-category">
  <a class="back-btn" href="{% url 'vocabulary_category_list' %}">← All Sections</a>
  <div class="cat-view-title-row" style="--accent-c:{{ category.color.bg_hex|default:'#7c3aed' }};">
    <span class="cat-view-icon"><svg class="ico" aria-hidden="true"><use href="#{{ category.icon|category_icon }}"/></svg></span>
    <div>
      <h1 class="cat-view-name">{{ category.name }}</h1>
      <p class="cat-view-sub">{{ all_word_ids|length }} words{% if category.section %} · {{ category.section.name }}{% endif %}</p>
    </div>
  </div>
  <div class="card-grid">
```

(This assumes `category.color` is already `select_related`-fetched by the existing `vocab_category` view, which it is — confirmed in `config/views_vocab.py`'s `Category.objects.select_related('cefr_level', 'color')` call. `all_word_ids` is likewise already in the existing view's context, computed for the bulk-action buttons.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_vocab_pages.py -k "vocabulary_category_detail_shows_section_header or vocabulary_category_detail_header_without_section" -v`
Expected: PASS.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass.

- [ ] **Step 6: Manual/Playwright verification**

Using a browser, navigate to a real category's word-list page from the newly section-grouped browse page. Confirm: "← All Sections" link returns to `/vocabulary/category/`, the category's own icon renders in the new icon badge (matching the icon already shown on its `.cat-card` on the browse page), and the meta line shows the correct word count and section name. Confirm both dark and light theme render this header correctly (it reuses the already-themed `.cat-view-*` CSS, so should need no new theme-specific rules — confirm this holds).

- [ ] **Step 7: Commit**

```bash
git add "VocabLarry Professional Environment/templates/vocab/category_word_list.html" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "feat(vlpe): add section-aware header to the category word-list drill-in page"
```
