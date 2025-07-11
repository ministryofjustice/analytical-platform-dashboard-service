from unittest.mock import patch

import pytest

from dashboard_service.users.models import User


@patch("django.db.models.Model.save", autospec=True)
def test_email_is_lowercased_on_save(mock_super_save):
    user = User(email="Test@Example.COM")
    user.save()

    assert user.email == "test@example.com"
    mock_super_save.assert_called_once()


def test_user_fields_in_memory():
    user = User(
        email="user@example.com",
        auth0_id="auth0|abc123",
        external_provider_id="abc123",
    )

    assert user.email == "user@example.com"
    assert user.auth0_id == "auth0|abc123"
    assert user.external_provider_id == "abc123"


@pytest.mark.django_db
def test_create_user_sets_password_correctly():
    user = User.objects.create_user(email="test@example.com", password="securepass")
    assert user.check_password("securepass")


@pytest.mark.django_db
def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(email="admin@example.com", password="adminpass")

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_active is True
