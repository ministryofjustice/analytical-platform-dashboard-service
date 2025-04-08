from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    """
    Index view for the dashboard service.
    """

    template_name = "dashboards/index.html"
