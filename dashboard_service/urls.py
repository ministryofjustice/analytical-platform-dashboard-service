"""
URL configuration for dashboard_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from dashboard_service import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("login/", views.login, name="login"),
    path("login-fail/", views.login_fail, name="login-fail"),
    path("logout/", views.logout, name="logout"),
    path("callback/", views.callback, name="callback"),
    path("dashboards/", include("dashboard_service.dashboards.urls", namespace="dashboards")),
    path("healthcheck/", views.healthcheck, name="healthcheck"),
]


if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    # Third-party
    from debug_toolbar.toolbar import debug_toolbar_urls  # noqa

    urlpatterns += debug_toolbar_urls()
    urlpatterns += [
        path("debug/404/", views.debug_404, name="debug-404"),
        path("debug/500/", views.debug_500, name="debug-500"),
    ]
