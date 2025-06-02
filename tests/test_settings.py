from django.conf import settings

from dashboard_service.settings.common import MIDDLEWARE


def test_login_required_middleware_enabled():
    assert "django.contrib.auth.middleware.LoginRequiredMiddleware" in MIDDLEWARE


def test_session_cookie_age():
    assert settings.SESSION_COOKIE_AGE == 86400


def test_login_prompt_set():
    assert settings.AUTHLIB_OAUTH_CLIENTS["auth0"]["client_kwargs"]["prompt"] == "login"
