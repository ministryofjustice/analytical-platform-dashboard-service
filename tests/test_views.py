from unittest.mock import Mock, patch

import pytest
from authlib.integrations.django_client import OAuthError
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.http import urlencode

from dashboard_service.users.models import User
from dashboard_service.views import callback, login, logout


@pytest.mark.parametrize(
    "next_url, expected_next",
    [
        ("", None),
        ("/some/next/url/", "/some/next/url/"),
        (None, None),
        ("https://malicious-url.com", None),  # Should not allow external URLs
    ],
    ids=["next_empty", "next_valid", "next_none", "next_malicious"],
)
@patch("dashboard_service.views.reverse", return_value="/callback/")
def test_login_calls_authorize_redirect_correctly(
    mock_reverse, next_url, expected_next, mock_auth0, rf
):
    query_params = {"next": next_url} if next_url else {}
    request = rf.get("/login/", query_params=query_params)
    request.user = AnonymousUser()
    redirect_url = "http://testserver/callback/"
    request.build_absolute_uri = Mock(return_value=redirect_url)

    login(request)
    if expected_next:
        redirect_url = f"{redirect_url}?{urlencode(query_params)}"

    mock_auth0.authorize_redirect.assert_called_once_with(request, redirect_url)
    mock_reverse.assert_called_once_with("callback")


@pytest.mark.parametrize(
    "next_url, expected_redirect",
    [
        ("", settings.LOGIN_REDIRECT_URL),
        ("/some/next/url/", "/some/next/url/"),
        (None, settings.LOGIN_REDIRECT_URL),
        ("https://malicious-url.com", settings.LOGIN_REDIRECT_URL),
    ],
    ids=["next_empty", "next_filled", "no_next", "malicious_url"],
)
@patch("dashboard_service.views._login")
@patch("dashboard_service.views.get_or_create_user_from_id_token")
def test_callback_authenticates_and_redirects(
    mock_get_or_update, mock_login, next_url, expected_redirect, rf, mock_auth0
):
    query_params = {"next": next_url} if next_url else {}
    request = rf.get("/callback/", query_params=query_params)
    user = Mock()
    mock_get_or_update.return_value = user
    token = {"userinfo": {"nickname": "testuser", "email": "test@example.com"}}
    mock_auth0.authorize_access_token.return_value = token

    response = callback(request)

    mock_auth0.authorize_access_token.assert_called_once_with(request)
    mock_get_or_update.assert_called_once_with(token["userinfo"])
    mock_login.assert_called_once_with(request, user=user)
    assert response.status_code == 302
    assert response.url == expected_redirect


@patch("dashboard_service.views._login")
@patch("dashboard_service.views.get_or_create_user_from_id_token")
def test_callback_redirects_to_login_fail_on_exception(
    mock_get_or_create, mock_login, rf, mock_auth0
):
    request = rf.get("/callback/")

    mock_auth0.authorize_access_token.side_effect = OAuthError("Error")

    response = callback(request)

    assert response.status_code == 302
    assert response.url == reverse("login-fail")
    mock_get_or_create.assert_not_called()
    mock_login.assert_not_called()


@patch("dashboard_service.views.urlencode")
@patch("dashboard_service.views._logout")
def test_logout_redirects_to_auth0(mock_logout, mock_urlencode, rf):
    request = rf.get("/logout/")
    request.build_absolute_uri = Mock(return_value="http://testserver/")
    mock_urlencode.return_value = "returnTo=http://testserver/&client_id=test-client-id"

    response = logout(request)

    mock_logout.assert_called_once_with(request)
    mock_urlencode.assert_called_once_with(
        {
            "returnTo": "http://testserver/",
            "client_id": "test-client-id",
        }
    )
    assert response.status_code == 302
    assert (
        response.url
        == "https://test.eu.auth0.com/v2/logout?returnTo=http://testserver/&client_id=test-client-id"
    )


class TestLoginFailView:
    def test_renders_template(self, client):
        url = reverse("login-fail")
        response = client.get(url)

        assert response.status_code == 200
        assert "login/login_fail.html" in [t.name for t in response.templates]

    @pytest.mark.django_db
    def test_redirects_if_authenticated(self, client):
        url = reverse("login-fail")
        user = User.objects.create(email="testuser@example.com")
        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 302
        assert reverse("dashboards:index") in response.url
