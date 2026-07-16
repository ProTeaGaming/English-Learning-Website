from django.db import migrations

# Each entry: pk -> (old values to restore on reverse, new values to set forward)
FIXES = {
    6129: {
        'old': {'word': 'flat', 'synonyms': ['apartment', 'unit'],
                'example': 'She lives in a small <em>flat</em> in the city centre.'},
        'new': {'word': 'apartment', 'synonyms': ['flat', 'unit'],
                'example': 'She lives in a small <em>apartment</em> in the city centre.'},
    },
    9274: {
        'old': {'word': 'biscuit', 'synonyms': ['cookie'],
                'example': 'She offered him a <em>biscuit</em> with his tea.'},
        'new': {'word': 'cookie', 'synonyms': ['biscuit'],
                'example': 'She offered him a <em>cookie</em> with his tea.'},
    },
    9336: {
        'old': {'word': 'holiday', 'synonyms': ['vacation', 'break', 'time off', 'leave', 'trip'],
                'example': "We're going on <em>holiday</em> next month."},
        'new': {'word': 'vacation', 'synonyms': ['holiday', 'break', 'time off', 'leave', 'trip'],
                'example': "We're going on <em>vacation</em> next month."},
    },
    9050: {
        'old': {'word': 'trousers', 'synonyms': ['pants', 'jeans', 'slacks'],
                'example': 'He wears <em>trousers</em> to the office.'},
        'new': {'word': 'pants', 'synonyms': ['trousers', 'jeans', 'slacks'],
                'example': 'He wears <em>pants</em> to the office.'},
    },
    8994: {
        'old': {'word': 'rubbish', 'synonyms': ['trash', 'garbage', 'waste', 'litter'],
                'example': 'Please put your <em>rubbish</em> in the bin.'},
        'new': {'word': 'garbage', 'synonyms': ['rubbish', 'trash', 'waste', 'litter'],
                'example': 'Please put your <em>garbage</em> in the trash can.'},
    },
    9269: {
        'old': {'word': 'queue', 'synonyms': ['line', 'row', 'wait', 'snake'],
                'example': 'There was a long <em>queue</em> at the checkout.'},
        'new': {'word': 'line', 'synonyms': ['queue', 'row', 'wait', 'snake'],
                'example': 'There was a long <em>line</em> at the checkout.'},
    },
    6377: {
        'old': {'word': 'film', 'definition': 'A story told through moving pictures; a movie.',
                'synonyms': ['movie', 'motion picture', 'cinema', 'flick'],
                'example': "What's your favourite <em>film</em>?"},
        'new': {'word': 'movie', 'definition': 'A story told through moving pictures; a film.',
                'synonyms': ['film', 'motion picture', 'cinema', 'flick'],
                'example': "What's your favorite <em>movie</em>?"},
    },
    6135: {
        'old': {'word': 'garden', 'synonyms': ['yard', 'lawn', 'plot'],
                'example': 'She grows vegetables in the <em>garden</em>.'},
        'new': {'word': 'yard', 'synonyms': ['garden', 'lawn', 'plot'],
                'example': 'She grows vegetables in the <em>yard</em>.'},
    },
    8995: {
        'old': {'word': 'bin', 'definition': 'A container for waste or rubbish.',
                'synonyms': ['dustbin', 'trash can', 'waste basket', 'skip'],
                'example': 'Throw the empty can in the <em>bin</em>.'},
        'new': {'word': 'trash can', 'definition': 'A container for waste or garbage.',
                'synonyms': ['bin', 'dustbin', 'waste basket', 'skip'],
                'example': 'Throw the empty can in the <em>trash can</em>.'},
    },
    9204: {
        'old': {'word': 'rubber', 'synonyms': ['eraser', 'correction tool'],
                'example': 'Can I borrow your <em>rubber</em>?'},
        'new': {'word': 'eraser', 'synonyms': ['rubber', 'correction tool'],
                'example': 'Can I borrow your <em>eraser</em>?'},
    },
    9053: {
        'old': {'word': 'shoes', 'definition': 'Items worn on your feet.',
                'synonyms': ['boots', 'trainers', 'footwear'],
                'example': 'She bought new <em>shoes</em> for the party.'},
        'new': {'word': 'sneakers',
                'definition': 'Casual athletic shoes worn for sport or everyday wear.',
                'synonyms': ['trainers', 'shoes', 'footwear'],
                'example': 'She bought new <em>sneakers</em> for the gym.'},
    },
    # candy (pk 9276) needs no DB change — the US headword was already correct.
}


def apply_fixes(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    for pk, change in FIXES.items():
        Word.objects.filter(pk=pk).update(**change['new'])


def revert_fixes(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    for pk, change in FIXES.items():
        Word.objects.filter(pk=pk).update(**change['old'])


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0005_alter_grammartopic_stage'),
    ]

    operations = [
        migrations.RunPython(apply_fixes, revert_fixes),
    ]
