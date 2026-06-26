import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def User():
    return get_user_model()


@pytest.fixture
def regular_user(db):
    U = get_user_model()
    return U.objects.create_user(
        email='user@example.com', username='regularuser',
        password='testpass123', role='user',
    )


@pytest.fixture
def staff_user(db):
    U = get_user_model()
    return U.objects.create_user(
        email='staff@example.com', username='staffuser',
        password='testpass123', role='staff',
    )


@pytest.fixture
def admin_user(db):
    U = get_user_model()
    return U.objects.create_user(
        email='admin@example.com', username='adminuser',
        password='testpass123', role='admin',
    )
