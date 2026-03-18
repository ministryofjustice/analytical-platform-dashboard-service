import requests
import structlog
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from dashboard_service.dashboards.api import api_client

logger = structlog.get_logger(__name__)


class IndexView(TemplateView):
    """
    Index view for the dashboard service.
    """

    template_name = "dashboards/index.html"

    def build_pagination_data(self, api_response):
        dashboard_url = reverse("dashboards:index")
        if not api_response["next"] and not api_response["previous"]:
            return None

        shared_via = self.request.GET.get("shared_via", None)
        shared_via_param = f"&shared_via={shared_via}" if shared_via else ""

        page_data = [
            {
                "number": page_number,
                "url": f"{dashboard_url}?page={page_number}{shared_via_param}"
                if isinstance(page_number, int)
                else None,
                "is_elipsis": not isinstance(page_number, int),
            }
            for page_number in api_response["page_numbers"]
        ]

        pagination_data = {
            "next": None,
            "previous": None,
            "current_page": api_response["current_page"],
            "page_data": page_data,
            "count": api_response["count"],
        }

        if api_response["next"]:
            pagination_data["next"] = (
                f"{dashboard_url}?page={api_response['current_page'] + 1}{shared_via_param}"
            )

        if api_response["previous"]:
            pagination_data["previous"] = (
                f"{dashboard_url}?page={api_response['current_page'] - 1}{shared_via_param}"
            )
        return pagination_data

    def get_api_response(self, shared_via=None, page=1):
        shared_via_mapping = {
            "direct": ["viewer", "admin"],
            "domain": ["domain"],
        }
        page = int(page) if page else 1
        response = api_client.make_request(
            "dashboards",
            params={
                "email": self.request.user.email,
                "shared_via": shared_via_mapping.get(shared_via),
                "page": page,
                "page_size": 10,
            },
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        shared_via = self.request.GET.get("shared_via", "direct")
        other = "domain" if shared_via == "direct" else "direct"
        page = self.request.GET.get("page", 1)
        email_domain = self.request.user.email.split("@")[-1]

        active = self.get_api_response(shared_via=shared_via, page=page)
        inactive = self.get_api_response(shared_via=other, page=1)

        context["dashboards"] = active["results"]
        context["pagination"] = self.build_pagination_data(active)
        context[f"{shared_via}_dashboards_count"] = active["count"]
        context[f"{other}_dashboards_count"] = inactive["count"]
        context["email_domain"] = email_domain
        context["domain_active"] = shared_via == "domain"
        logger.info("dashboard_list_retrieved")
        return context


class DetailView(TemplateView):
    template_name = "dashboards/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            dashboard_data = api_client.make_request(
                f"dashboards/{self.kwargs['quicksight_id']}",
                params={"email": self.request.user.email},
                timeout=5,
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Http404("Dashboard not found") from e
            raise e
        context["dashboard"] = dashboard_data
        context["dashboard_admins"] = ", ".join(
            [admin["email"] for admin in dashboard_data["admins"]]
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        dashboard_data = context.get("dashboard", {})
        logger.info(
            "dashboard_viewed",
            dashboard_name=dashboard_data.get("name"),
            user_arn=dashboard_data.get("anonymous_user_arn"),
        )
        return response
