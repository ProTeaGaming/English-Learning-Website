from django.db import migrations

# (pk, word, pos, definition, example, synonyms, antonyms, category_slug, cefr_code)
# Explicit pks continue the existing sequence (current max is 9920) so this
# plan can reference exact WORD_GB keys below without a runtime lookup step.
NEW_WORDS = [
    (9921, 'eggplant', 'noun', 'A purple vegetable with a smooth, shiny skin.',
     'She grilled some <em>eggplant</em> for dinner.', ['aubergine'], [],
     'food-drink-basic', 'A1+'),
    (9922, 'zucchini', 'noun', 'A long green vegetable similar to a cucumber.',
     'He sliced the <em>zucchini</em> for the stir-fry.', ['courgette'], [],
     'food-drink-basic', 'A1+'),
    (9923, 'diaper', 'noun', 'A piece of soft material worn by babies to absorb waste.',
     "She changed the baby's <em>diaper</em> before bed.", ['nappy'], [],
     'home-household', 'A1'),
    (9924, 'sweater', 'noun', 'A warm knitted garment worn on the upper body.',
     'He put on a <em>sweater</em> because it was cold.', ['jumper', 'pullover'], [],
     'a1plus-clothes-appearance', 'A1'),
    (9925, 'flashlight', 'noun', 'A small portable light powered by batteries.',
     'She used a <em>flashlight</em> to find her keys in the dark.', ['torch'], [],
     'a1plus-home-objects', 'A1+'),
    (9926, 'gasoline', 'noun', 'A fuel used to power most cars.',
     'The car ran out of <em>gasoline</em> on the highway.', ['petrol', 'fuel'], [],
     'travel-experiences', 'A2'),
    (9927, 'sidewalk', 'noun', 'A paved path for walking beside a road.',
     'Children were playing on the <em>sidewalk</em>.', ['pavement'], [],
     'travel-experiences', 'A1'),
    (9928, 'faucet', 'noun', 'A device that controls the flow of water from a pipe.',
     'She turned off the <em>faucet</em> after washing her hands.', ['tap'], [],
     'a1plus-home-objects', 'A1+'),
    (9929, 'parking lot', 'noun', 'An area where vehicles can be parked.',
     'We left the car in the <em>parking lot</em> near the mall.', ['car park'], [],
     'travel-experiences', 'A2'),
    (9930, 'mailbox', 'noun', 'A box where letters and packages are delivered.',
     'He checked the <em>mailbox</em> for new mail.', ['postbox'], [],
     'a1plus-home-objects', 'A1+'),
    (9931, 'cell phone', 'noun', 'A portable telephone used for calls and messaging.',
     'She left her <em>cell phone</em> at home by mistake.', ['mobile phone', 'cellphone'], [],
     'technology-modern-life', 'A1'),
    (9932, 'resume', 'noun', "A document summarizing a person's work experience and skills.",
     'He updated his <em>resume</em> before applying for the job.', ['CV', 'curriculum vitae'], [],
     'work-career', 'B1'),
    (9933, 'stroller', 'noun', 'A wheeled chair used to push a young child.',
     'She pushed the <em>stroller</em> through the park.', ['pram', 'buggy'], [],
     'home-household', 'A2'),
    (9934, 'pacifier', 'noun', 'A rubber or plastic nipple given to a baby to suck on.',
     'The baby calmed down once given a <em>pacifier</em>.', ['dummy', 'soother'], [],
     'home-household', 'A2+'),
    (9935, 'band-aid', 'noun', 'A small adhesive strip used to cover minor cuts.',
     'She put a <em>band-aid</em> on her scraped knee.', ['plaster'], [],
     'body-health-basic', 'A1'),
    (9936, 'crib', 'noun', 'A small bed with high sides for a baby.',
     'The baby slept peacefully in her <em>crib</em>.', ['cot'], [],
     'home-household', 'A2'),
    (9937, 'elevator', 'noun', 'A machine that carries people between floors of a building.',
     'They took the <em>elevator</em> to the tenth floor.', ['lift'], ['stairs'],
     'a1plus-home-objects', 'A1'),
    (9938, 'math', 'noun', 'The study of numbers, quantities, and shapes.',
     "She's always been good at <em>math</em>.", ['maths', 'mathematics'], [],
     'numbers-school-basic', 'A1'),
]


def add_words(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    Category = apps.get_model('vocab', 'Category')
    CEFRLevel = apps.get_model('vocab', 'CEFRLevel')

    for pk, word, pos, definition, example, synonyms, antonyms, cat_slug, cefr_code in NEW_WORDS:
        category = Category.objects.get(slug=cat_slug)
        cefr = CEFRLevel.objects.get(code=cefr_code)
        max_order = Word.objects.filter(category=category).order_by('-order').first()
        next_order = (max_order.order + 1) if max_order else 0
        Word.objects.create(
            pk=pk, word=word, pos=pos, definition=definition, example=example,
            synonyms=synonyms, antonyms=antonyms,
            category=category, cefr_level=cefr, order=next_order,
        )


def remove_words(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    Word.objects.filter(pk__in=[w[0] for w in NEW_WORDS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0006_fix_us_uk_word_pairs'),
    ]

    operations = [
        migrations.RunPython(add_words, remove_words),
    ]
