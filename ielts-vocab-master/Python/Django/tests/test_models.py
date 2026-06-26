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
