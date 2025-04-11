from dashboard_service.settings.common import MIDDLEWARE


def test_login_required_middleware_enabled():
    assert "django.contrib.auth.middleware.LoginRequiredMiddleware" in MIDDLEWARE
