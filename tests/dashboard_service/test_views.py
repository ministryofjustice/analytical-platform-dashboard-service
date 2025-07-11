from unittest.mock import patch

import pytest
import requests
from django.conf import settings
from django.http import Http404
from django.urls import reverse

from dashboard_service.dashboards import views
from dashboard_service.users.models import User


@pytest.fixture
def user():
    return User(email="test@example.com")


@pytest.fixture(autouse=True)
def authenticated_api_client(api_client):
    """
    Patch the api_client to always return a valid token
    """
    with patch.object(api_client, "token_expired", return_value=False):
        yield api_client


class TestIndexView:
    @pytest.fixture
    def view_obj(self, rf):
        """
        Fixture to create an instance of IndexView with a request object
        """
        request = rf.get(reverse("dashboards:index"))
        view_obj = views.IndexView()
        view_obj.request = request
        yield view_obj

    def test_index_requires_login(self, client):
        url = reverse("dashboards:index")

        response = client.get(url)

        assert response.status_code == 302
        assert response.url == f"{settings.LOGIN_URL}?next={url}"

    @pytest.mark.django_db
    def test_login_required(self, client, user):
        url = reverse("dashboards:index")
        user.save()
        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 200
        assert "dashboards/index.html" in [t.name for t in response.templates]

    def test_get_context_data(self, api_client, view_obj, user, caplog):
        caplog.set_level("INFO", logger="dashboard_service")
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = {
                "results": [
                    {
                        "name": "test-dashboard",
                        "quicksight_id": "123456789",
                        "admins": [{"name": "test_user", "email": "test.user@justice.gov.uk"}],
                    }
                ],
                "next": None,
                "previous": None,
            }
            context = view_obj.get_context_data()

        assert "dashboards" in context
        assert "pagination" not in context
        mock_make_request.assert_called_once_with("dashboards", params={"email": user.email})
        assert any("dashboard_list_retrieved" in rec.getMessage() for rec in caplog.records)

    def test_get_context_data_pagination(self, api_client, view_obj, user, caplog):
        caplog.set_level("INFO", logger="dashboard_service")
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = {
                "results": [
                    {
                        "name": "test-dashboard",
                        "quicksight_id": "123456789",
                        "admins": [{"name": "test_user", "email": "test.user@justice.gov.uk"}],
                    }
                ],
                "next": "next_link",
                "previous": None,
                "page_numbers": [1, 2, 3],
                "current_page": 1,
                "count": 30,
            }
            context = view_obj.get_context_data()

        assert "dashboards" in context
        assert "pagination" in context
        mock_make_request.assert_called_once_with("dashboards", params={"email": user.email})
        assert any("dashboard_list_retrieved" in rec.getMessage() for rec in caplog.records)


class TestDetailView:
    @pytest.fixture
    def view_obj(self, rf):
        """
        Fixture to create an instance of IndexView with a request object
        """
        request = rf.get(reverse("dashboards:index"))
        view_obj = views.DetailView(kwargs={"quicksight_id": "test_id"})
        view_obj.request = request
        yield view_obj

    @pytest.mark.django_db
    def test_login_required(self, client, user):
        url = reverse("dashboards:detail", kwargs={"quicksight_id": "test_id"})
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == f"{settings.LOGIN_URL}?next={url}"

        user.save()
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert "dashboards/detail.html" in response.template_name

    def test_get_context_data(self, api_client, view_obj, user):
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            context = view_obj.get_context_data()

        assert "dashboard" in context
        mock_make_request.assert_called_once_with(
            f"dashboards/{view_obj.kwargs['quicksight_id']}",
            params={"email": user.email},
            timeout=5,
        )

    def test_404_raised(self, api_client, view_obj, user):
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.side_effect = requests.exceptions.HTTPError(
                response=type("Response", (object,), {"status_code": 404})
            )

            with pytest.raises(Http404):
                view_obj.get_context_data()

    def test_other_http_error(self, api_client, view_obj, user):
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.side_effect = requests.exceptions.HTTPError(
                response=type("Response", (object,), {"status_code": 500})
            )

            with pytest.raises(requests.exceptions.HTTPError):
                view_obj.get_context_data()

    def test_render_to_response(self, api_client, view_obj, user, caplog):
        caplog.set_level("INFO", logger="dashboard_service")
        with patch("django.views.generic.TemplateView.render_to_response") as mock_render:
            response = view_obj.render_to_response({})

        assert any("dashboard_viewed" in rec.getMessage() for rec in caplog.records)
        mock_render.assert_called_once()
        assert response == mock_render.return_value
