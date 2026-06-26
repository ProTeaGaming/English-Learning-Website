import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_custom_user_email_is_username_field():
    User = get_user_model()
    assert User.USERNAME_FIELD == 'email'


@pytest.mark.django_db
def test_create_user_sets_default_role(db):
    User = get_user_model()
    u = User.objects.create_user(
        email='test@example.com', username='tester', password='pw123456'
    )
    assert u.role == 'user'


@pytest.mark.django_db
def test_learn_map_defaults_to_empty_dict(db):
    User = get_user_model()
    u = User.objects.create_user(
        email='map@example.com', username='mapper', password='pw123456'
    )
    assert u.learn_map == {}


@pytest.mark.django_db
def test_role_choices_exist():
    User = get_user_model()
    roles = [r[0] for r in User.Role.choices]
    assert 'user' in roles
    assert 'staff' in roles
    assert 'admin' in roles


import pytest
from vocab.models import CEFRLevel, Color, Category, Word


@pytest.mark.django_db
def test_cefr_level_str():
    level = CEFRLevel.objects.create(code='B2', name='Upper-Intermediate', order=4)
    assert str(level) == 'B2'


@pytest.mark.django_db
def test_category_requires_unique_slug(db):
    from django.db import IntegrityError
    CEFRLevel.objects.create(code='A1', name='Beginner', order=1)
    Category.objects.create(slug='test-cat', name='Test')
    with pytest.raises(IntegrityError):
        Category.objects.create(slug='test-cat', name='Duplicate')


@pytest.mark.django_db
def test_word_synonyms_defaults_to_list(db):
    level = CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)
    cat = Category.objects.create(slug='test', name='Test')
    w = Word.objects.create(
        word='Tenacious', definition='Not giving up easily.', category=cat
    )
    assert w.synonyms == []
    assert w.antonyms == []


@pytest.mark.django_db
def test_deleting_category_cascades_to_words(db):
    cat = Category.objects.create(slug='cascade-test', name='Cascade')
    Word.objects.create(word='Example', definition='A word.', category=cat)
    cat.delete()
    assert Word.objects.count() == 0
