import json
import pytest
from django.test import Client
from vocab.models import CEFRLevel, Color, Category, Word


@pytest.fixture
def sample_data(db):
    level = CEFRLevel.objects.create(code='B2', name='Upper-Intermediate', order=4)
    color = Color.objects.create(name='Blue', bg_hex='#3b82f6', text_hex='#ffffff')
    cat = Category.objects.create(
        slug='strength', name='Strength', icon='💪', cefr_level=level, color=color
    )
    word = Word.objects.create(
        word='Tenacious', pos='adj', definition='Not giving up.',
        synonyms=['persistent'], antonyms=['weak'], example='She was tenacious.',
        gap='She was ___ in her pursuit.', category=cat, cefr_level=level, order=0
    )
    return {'level': level, 'color': color, 'cat': cat, 'word': word}


@pytest.mark.django_db
def test_words_endpoint_returns_list(sample_data):
    c = Client()
    r = c.get('/api/words/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert len(data) == 1
    assert data[0]['word'] == 'Tenacious'
    assert data[0]['pos'] == 'adj'
    assert data[0]['synonyms'] == ['persistent']
    assert data[0]['category_id'] == sample_data['cat'].id


@pytest.mark.django_db
def test_categories_endpoint_returns_list(sample_data):
    c = Client()
    r = c.get('/api/categories/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert len(data) == 1
    assert data[0]['slug'] == 'strength'
    assert data[0]['bg_hex'] == '#3b82f6'
    assert data[0]['cefr_level_id'] == sample_data['level'].id
    assert data[0]['color_id'] == sample_data['color'].id


@pytest.mark.django_db
def test_cefr_levels_endpoint_returns_ordered_list(db):
    CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)
    CEFRLevel.objects.create(code='A1', name='Beginner', order=1)
    c = Client()
    r = c.get('/api/cefr-levels/')
    data = json.loads(r.content)
    assert data[0]['code'] == 'A1'
    assert data[1]['code'] == 'B1'
