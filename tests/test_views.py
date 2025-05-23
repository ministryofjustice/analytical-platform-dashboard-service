from unittest.mock import Mock, patch

import pytest
from authlib.integrations.django_client import OAuthError
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from dashboard_service.users.models import User
from dashboard_service.views import callback, login, logout


@patch("dashboard_service.views.reverse", return_value="/callback/")
def test_login_calls_authorize_redirect_correctly(mock_reverse, mock_auth0, rf):
    request = rf.get("/login/")
    request.user = AnonymousUser()
    expected_redirect_uri = "http://testserver/callback/"
    request.build_absolute_uri = Mock(return_value=expected_redirect_uri)

    login(request)

    mock_auth0.authorize_redirect.assert_called_once_with(request, expected_redirect_uri)
    mock_reverse.assert_called_once_with("callback")


@patch("dashboard_service.views._login")
@patch("dashboard_service.views.User.objects.get_or_create")
def test_callback_authenticates_and_redirects(mock_get_or_create, mock_login, rf, mock_auth0):
    request = rf.get("/callback/")
    user = Mock()
    mock_get_or_create.return_value = (user, True)
    mock_auth0.authorize_access_token.return_value = {
        "userinfo": {"nickname": "testuser", "email": "test@example.com"}
    }

    response = callback(request)

    mock_auth0.authorize_access_token.assert_called_once_with(request)
    mock_get_or_create.assert_called_once_with(
        username="testuser", defaults={"email": "test@example.com"}
    )
    mock_login.assert_called_once_with(request, user=user)
    assert response.status_code == 302
    assert response.url == "/dashboards/"


@patch("dashboard_service.views._login")
@patch("dashboard_service.views.User.objects.get_or_create")
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
        user = User.objects.create(username="testuser", email="testuser@example.com")
        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 302
        assert reverse("dashboards:index") in response.url
