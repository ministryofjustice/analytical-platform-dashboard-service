import requests
from django.http import Http404
from django.views.generic import TemplateView

from dashboard_service.dashboards.api import api_client


class IndexView(TemplateView):
    """
    Index view for the dashboard service.
    """

    template_name = "dashboards/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboards"] = api_client.make_request(
            "dashboards", params={"email": self.request.user.email}
        )["results"]
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
