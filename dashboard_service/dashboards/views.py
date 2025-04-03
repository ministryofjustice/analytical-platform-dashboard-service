from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class Index(LoginRequiredMixin, TemplateView):
    """
    Index view for the dashboard service.
    """

    template_name = "dashboards/index.html"
