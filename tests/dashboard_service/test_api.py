import time
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings


def test_get_access_token(api_client, mock_requests):
    """
    Test that get_access_token makes the correct request to Auth0 and returns the response.
    """
    mock_token_data = {
        "access_token": "mock_token_123",
        "expires_in": 86400,  # 24 hours in seconds
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_token_data
    mock_requests.post.return_value = mock_response

    result = api_client.get_access_token()

    assert result == mock_token_data
    mock_requests.post.assert_called_once_with(
        url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
        data={
            "client_id": settings.AUTH0_CLIENT_ID,
            "client_secret": settings.AUTH0_CLIENT_SECRET,
            "audience": settings.AUTH0_AUDIENCE,
            "grant_type": "client_credentials",
        },
    )
    mock_response.json.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.parametrize(
    "access_token, token_expiry, expected",
    [
        (None, None, True),
        ("mock_token_123", None, True),
        (None, 1234567890, True),
        ("mock_token_123", 1000000000, True),
        ("mock_token_123", int(time.time()) + 290, True),  # within the 5 min buffer
        ("mock_token_123", int(time.time()) + 500, False),  # valid token
    ],
)
def test_token_expired(access_token, token_expiry, expected, api_client):
    api_client.access_token = access_token
    api_client.token_expiry = token_expiry
    assert api_client.token_expired() is expected


def test_ensure_valid_token_token_valid(api_client):
    with patch.object(api_client, "token_expired", return_value=False):
        api_client.access_token = "mock_token_123"
        assert api_client.ensure_valid_token() == "mock_token_123"
        api_client.token_expired.assert_called_once()


def test_ensure_valid_token_token_expired(api_client):
    api_client.access_token = None
    with patch.object(api_client, "get_access_token") as mock_get_access_token:
        mock_get_access_token.return_value = {
            "access_token": "mock_token_456",
            "expires_in": 86400,
        }
        assert api_client.ensure_valid_token() == "mock_token_456"
        mock_get_access_token.assert_called_once()
        assert api_client.access_token == "mock_token_456"
        assert api_client.token_expiry == int(time.time()) + 86400


@pytest.mark.parametrize(
    "endpoint, method, params",
    [
        ("mock_endpoint", "GET", {}),
        ("mock_endpoint", "POST", {}),
        ("mock_endpoint", "PUT", {}),
        ("mock_endpoint", "DELETE", {}),
        ("mock_endpoint", "GET", {"param1": "test1", "param2": "test2"}),
    ],
)
def test_make_request(endpoint, method, params, api_client, mock_requests):
    """
    Test that make_request calls the requests library with the correct parameters.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_requests.request.return_value = mock_response
    api_client.access_token = "mock_token_123"

    with patch.object(api_client, "ensure_valid_token", return_value="mock_token_123"):
        result = api_client.make_request(endpoint, method=method, **params)

        assert result == {"key": "value"}
        mock_requests.request.assert_called_once_with(
            method,
            f"{api_client.base_url}{endpoint}",
            headers={"Authorization": f"Bearer {api_client.access_token}"},
            **params,
        )
