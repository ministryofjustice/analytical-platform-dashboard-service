import pytest
from django.conf import settings
from django.urls import reverse

from dashboard_service.users.models import User


@pytest.mark.django_db
class TestIndexView:
    def test_index_requires_login(self, client):
        url = reverse("dashboards:index")

        response = client.get(url)

        assert response.status_code == 302
        assert settings.LOGIN_URL in response.url

    def test_index_returns_200_for_authenticated_user(self, client):
        url = reverse("dashboards:index")
        user = User.objects.create(username="testuser", email="test@example.com")
        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 200
        assert "dashboards/index.html" in [t.name for t in response.templates]
