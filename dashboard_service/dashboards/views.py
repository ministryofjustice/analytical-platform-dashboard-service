import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView

from dashboard_service.dashboards.api import api_client


class IndexView(LoginRequiredMixin, TemplateView):
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


class DetailView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["dashboard"] = api_client.make_request(
                f"dashboards/{kwargs['quicksight_id']}", params={"email": self.request.user.email}
            )
        except requests.exceptions.HTTPError as e:
            raise Http404() from e
        return context
