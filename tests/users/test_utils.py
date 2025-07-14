from unittest.mock import MagicMock, patch

import pytest

from dashboard_service.users.models import User
from dashboard_service.users.utils import get_or_create_user_from_id_token


@pytest.fixture
def id_token_factory():
    def _make(sub="auth0|abc123", email="user@example.com"):
        return {
            "sub": sub,
            "email": email,
        }

    return _make


@patch("dashboard_service.users.models.User.objects.get")
def test_returns_existing_user_by_auth0_id(mock_get, id_token_factory):
    mock_user = MagicMock(spec=User)
    mock_user.email = "user@example.com"
    mock_get.return_value = mock_user

    id_token = id_token_factory()
    result = get_or_create_user_from_id_token(id_token)

    assert result is mock_user
    mock_get.assert_called_once_with(auth0_id="auth0|abc123")


@patch("dashboard_service.users.models.User.objects.update_or_create")
@patch("dashboard_service.users.models.User.objects.get", side_effect=User.DoesNotExist)
def test_creates_user_if_not_found(mock_get, mock_update_or_create, id_token_factory):
    mock_user = MagicMock(spec=User)
    mock_update_or_create.return_value = (mock_user, True)

    id_token = id_token_factory(sub="aad|xyz123", email="new@example.com")
    result = get_or_create_user_from_id_token(id_token)

    assert result is mock_user
    mock_update_or_create.assert_called_once_with(
        email="new@example.com",
        defaults={
            "auth0_id": "aad|xyz123",
            "external_provider_id": "xyz123",
        },
    )


@patch("dashboard_service.users.models.User.objects.get")
def test_updates_email_if_changed(mock_get, id_token_factory):
    mock_user = MagicMock(spec=User)
    mock_user.email = "old@example.com"
    mock_user.nickname = None
    mock_get.return_value = mock_user

    id_token = id_token_factory(email="updated@example.com")
    result = get_or_create_user_from_id_token(id_token)

    assert result.email == "updated@example.com"
    mock_user.save.assert_called_once()
