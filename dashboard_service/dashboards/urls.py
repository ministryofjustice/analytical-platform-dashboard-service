from django.urls import path

from . import views

app_name = "dashboards"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<str:quicksight_id>/", views.DetailView.as_view(), name="detail"),
]
