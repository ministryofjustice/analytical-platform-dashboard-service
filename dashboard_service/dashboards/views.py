import requests
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from dashboard_service.dashboards.api import api_client


class IndexView(TemplateView):
    """
    Index view for the dashboard service.
    """

    template_name = "dashboards/index.html"

    def build_pagination_data(self, response, context):
        if response["next"] or response["previous"]:
            page_data = [
                {
                    "number": page_number,
                    "url": f"{reverse('dashboards:index')}?page={page_number}"
                    if isinstance(page_number, int)
                    else None,
                    "is_elipsis": not isinstance(page_number, int),
                }
                for page_number in response["page_numbers"]
            ]

            context["pagination"] = {
                "next": response["next"],
                "previous": response["previous"],
                "current_page": response["current_page"],
                "page_data": page_data,
                "count": response["count"],
            }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page = self.request.GET.get("page", None)
        params = {
            "email": self.request.user.email,
        }

        if page is not None:
            params["page"] = page

        response = api_client.make_request("dashboards", params=params)
        context["dashboards"] = response["results"]
        self.build_pagination_data(response, context)

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
