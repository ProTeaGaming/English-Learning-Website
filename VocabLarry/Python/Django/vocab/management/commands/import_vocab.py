import json5
import pathlib
import re
from django.core.management.base import BaseCommand
from vocab.models import CEFRLevel, Color, Category, Word

# Colors sourced from React-Native/src/index.css .t-<code> rules
THEME_MAP = {
    'tr':    {'name': 'Red',          'bg_hex': '#ef4444', 'text_hex': '#ffffff'},
    'tg':    {'name': 'Gold',         'bg_hex': '#eab308', 'text_hex': '#1a1a1a'},
    'tro':   {'name': 'Rose',         'bg_hex': '#f43f5e', 'text_hex': '#ffffff'},
    'tb':    {'name': 'Blue',         'bg_hex': '#3b82f6', 'text_hex': '#ffffff'},
    'tp':    {'name': 'Pink',         'bg_hex': '#ec4899', 'text_hex': '#ffffff'},
    'tv':    {'name': 'Violet',       'bg_hex': '#8b5cf6', 'text_hex': '#ffffff'},
    'te':    {'name': 'Emerald',      'bg_hex': '#10b981', 'text_hex': '#ffffff'},
    'ta':    {'name': 'Amber',        'bg_hex': '#f59e0b', 'text_hex': '#1a1a1a'},
    'tc':    {'name': 'Cyan',         'bg_hex': '#06b6d4', 'text_hex': '#ffffff'},
    'ti':    {'name': 'Indigo',       'bg_hex': '#6366f1', 'text_hex': '#ffffff'},
    'to':    {'name': 'Orange',       'bg_hex': '#f97316', 'text_hex': '#ffffff'},
    'tfg':   {'name': 'Forest Green', 'bg_hex': '#16a34a', 'text_hex': '#ffffff'},
    'tpurp': {'name': 'Purple',       'bg_hex': '#a855f7', 'text_hex': '#ffffff'},
    'ts':    {'name': 'Teal',         'bg_hex': '#0d9488', 'text_hex': '#ffffff'},
}

CEFR_META = [
    ('A1', 'Beginner', 1),
    ('A2', 'Elementary', 2),
    ('B1', 'Intermediate', 3),
    ('B2', 'Upper-Intermediate', 4),
    ('C1', 'Advanced', 5),
    ('C2', 'Proficient', 6),
]


class Command(BaseCommand):
    help = 'Seed DB from React-Native JS data files. Idempotent.'

    def handle(self, *args, **options):
        self._seed_cefr()
        self._seed_colors()

        data_dir = pathlib.Path(__file__).resolve().parents[5] / 'React-Native' / 'src' / 'data'
        files = sorted(data_dir.glob('data-part*.js'))
        if not files:
            self.stderr.write(f'No data files found in {data_dir}')
            return

        cat_order = 0
        for path in files:
            raw = path.read_text(encoding='utf-8')
            # Strip JS export wrapper: export const PARTX = [...];
            # No ^ anchor — comment lines may precede the export statement
            raw = re.sub(r'export\s+const\s+\w+\s*=\s*', '', raw.strip())
            raw = raw.rstrip(';')
            categories = json5.loads(raw)
            for cat_data in categories:
                cat_order += 1
                self._import_category(cat_data, cat_order)

        self.stdout.write(self.style.SUCCESS(
            f'Done. Categories: {Category.objects.count()}, Words: {Word.objects.count()}'
        ))

    def _seed_cefr(self):
        for code, name, order in CEFR_META:
            CEFRLevel.objects.get_or_create(code=code, defaults={'name': name, 'order': order})

    def _seed_colors(self):
        for theme_code, attrs in THEME_MAP.items():
            Color.objects.get_or_create(name=attrs['name'], defaults={
                'bg_hex': attrs['bg_hex'], 'text_hex': attrs['text_hex']
            })

    def _import_category(self, data: dict, order: int):
        slug = data.get('id', '')
        if not slug:
            return

        theme = data.get('theme', '')
        color_name = THEME_MAP.get(theme, {}).get('name')
        color = Color.objects.filter(name=color_name).first() if color_name else None

        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name':  data.get('name', slug),
                'icon':  data.get('icon', ''),
                'color': color,
                'order': order,
            },
        )

        for word_order, w in enumerate(data.get('words', [])):
            cefr_code = w.get('cefr', '').rstrip('+')
            cefr = CEFRLevel.objects.filter(code=cefr_code).first()
            Word.objects.get_or_create(
                word=w.get('w', ''),
                category=cat,
                defaults={
                    'pos':        w.get('pos', ''),
                    'definition': w.get('def', ''),
                    'synonyms':   w.get('syn', []),
                    'antonyms':   w.get('ant', []),
                    'example':    w.get('ex', ''),
                    'gap':        w.get('gap', ''),
                    'cefr_level': cefr,
                    'order':      word_order,
                },
            )
