from django.views.generic import TemplateView


class Index(TemplateView):
    """
    Index view for the dashboard service.
    """

    template_name = "dashboards/index.html"
