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
                "count": 1,
            }
            context = view_obj.get_context_data()

        assert "dashboards" in context
        assert context["pagination"] is None
        assert mock_make_request.call_count == 2
        mock_make_request.assert_any_call(
            "dashboards",
            params={
                "email": user.email,
                "shared_via": ["viewer", "admin"],
                "page": 1,
                "page_size": 10,
            },
        )
        mock_make_request.assert_any_call(
            "dashboards",
            params={
                "email": user.email,
                "shared_via": ["domain"],
                "page": 1,
                "page_size": 10,
            },
        )
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
        assert context["pagination"] is not None
        assert mock_make_request.call_count == 2
        assert any("dashboard_list_retrieved" in rec.getMessage() for rec in caplog.records)

    def test_get_context_data_domain_tab(self, api_client, rf, user, caplog):
        """Test that domain tab uses domain response as active"""
        caplog.set_level("INFO", logger="dashboard_service")
        request = rf.get(reverse("dashboards:index"), {"shared_via": "domain"})
        request.user = user
        view_obj = views.IndexView()
        view_obj.request = request

        with patch.object(api_client, "make_request") as mock_make_request:
            direct_response = {
                "results": [{"name": "direct-dashboard", "quicksight_id": "111"}],
                "next": None,
                "previous": None,
                "count": 1,
            }
            domain_response = {
                "results": [{"name": "domain-dashboard", "quicksight_id": "222"}],
                "next": None,
                "previous": None,
                "count": 5,
            }
            mock_make_request.side_effect = [domain_response, direct_response]
            context = view_obj.get_context_data()

        assert context["dashboards"] == domain_response["results"]
        assert context["domain_dashboards_count"] == 5
        assert context["direct_dashboards_count"] == 1

    def test_get_context_data_page_forwarded_to_active_tab(self, api_client, rf, user):
        """Test that page param is forwarded to the active tab only"""
        request = rf.get(reverse("dashboards:index"), {"page": "3"})
        request.user = user
        view_obj = views.IndexView()
        view_obj.request = request

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = {
                "results": [],
                "next": None,
                "previous": None,
                "count": 0,
            }
            view_obj.get_context_data()

        # Active tab (direct) gets page=3, inactive (domain) gets page=1
        mock_make_request.assert_any_call(
            "dashboards",
            params={
                "email": user.email,
                "shared_via": ["viewer", "admin"],
                "page": 3,
                "page_size": 10,
            },
        )
        mock_make_request.assert_any_call(
            "dashboards",
            params={
                "email": user.email,
                "shared_via": ["domain"],
                "page": 1,
                "page_size": 10,
            },
        )

    def test_get_context_data_page_forwarded_to_domain_tab(self, api_client, rf, user):
        """Test that page param is forwarded to domain tab when active"""
        request = rf.get(reverse("dashboards:index"), {"shared_via": "domain", "page": "2"})
        request.user = user
        view_obj = views.IndexView()
        view_obj.request = request

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = {
                "results": [],
                "next": None,
                "previous": None,
                "count": 0,
            }
            view_obj.get_context_data()

        # Active tab (domain) gets page=2, inactive (direct) gets page=1
        mock_make_request.assert_any_call(
            "dashboards",
            params={
                "email": user.email,
                "shared_via": ["domain"],
                "page": 2,
                "page_size": 10,
            },
        )
        mock_make_request.assert_any_call(
            "dashboards",
            params={
                "email": user.email,
                "shared_via": ["viewer", "admin"],
                "page": 1,
                "page_size": 10,
            },
        )

    def test_get_context_data_context_keys(self, api_client, view_obj, user):
        """Test that all expected context keys are set"""
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = {
                "results": [],
                "next": None,
                "previous": None,
                "count": 7,
            }
            context = view_obj.get_context_data()

        assert context["direct_dashboards_count"] == 7
        assert context["domain_dashboards_count"] == 7
        assert context["email_domain"] == "example.com"

    def test_build_pagination_data_includes_shared_via_in_urls(self, api_client, rf, user):
        """Test that pagination URLs include shared_via param when on domain tab"""
        request = rf.get(reverse("dashboards:index"), {"shared_via": "domain"})
        request.user = user
        view_obj = views.IndexView()
        view_obj.request = request

        api_response = {
            "next": "next_link",
            "previous": "prev_link",
            "page_numbers": [1, 2, 3],
            "current_page": 2,
            "count": 30,
        }
        pagination = view_obj.build_pagination_data(api_response)

        assert "&shared_via=domain" in pagination["next"]
        assert "&shared_via=domain" in pagination["previous"]
        for page in pagination["page_data"]:
            if page["url"]:
                assert "&shared_via=domain" in page["url"]

    def test_build_pagination_data_no_shared_via_on_direct_tab(self, api_client, view_obj, user):
        """Test that pagination URLs don't include shared_via on the default tab"""
        view_obj.request.user = user

        api_response = {
            "next": "next_link",
            "previous": "prev_link",
            "page_numbers": [1, 2, 3],
            "current_page": 2,
            "count": 30,
        }
        pagination = view_obj.build_pagination_data(api_response)

        assert "shared_via" not in pagination["next"]
        assert "shared_via" not in pagination["previous"]

    def test_build_pagination_data_returns_none_when_no_pages(self, api_client, view_obj, user):
        """Test that build_pagination_data returns None when there's no pagination"""
        view_obj.request.user = user

        api_response = {
            "next": None,
            "previous": None,
            "count": 5,
        }
        assert view_obj.build_pagination_data(api_response) is None


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
    def test_login_required(self, client, user, api_client):
        url = reverse("dashboards:detail", kwargs={"quicksight_id": "test_id"})
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == f"{settings.LOGIN_URL}?next={url}"

        user.save()
        client.force_login(user)
        with patch.object(api_client, "make_request", return_value={}):
            response = client.get(url)

        assert response.status_code == 200
        assert "dashboards/detail.html" in response.template_name

    def test_get_context_data(self, api_client, view_obj, user):
        view_obj.request.user = user

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = {}
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
