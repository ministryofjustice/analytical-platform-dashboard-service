import sentry_sdk
from authlib.integrations.django_client import OAuth, OAuthError
from django.conf import settings
from django.contrib.auth import login as _login
from django.contrib.auth import logout as _logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from dashboard_service.users.models import User

oauth = OAuth()
oauth.register(
    "auth0",
)


# TODO add frontpage view e.g. with login button
@login_not_required
def index(request):
    """
    Index view for the dashboard service.
    """
    if request.user.is_authenticated:
        return redirect(reverse("dashboards:index"))
    return redirect(reverse("login"))


@login_not_required
def login(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboards:index"))
    redirect_uri = request.build_absolute_uri(reverse("callback"))
    return oauth.auth0.authorize_redirect(request, redirect_uri)


@login_not_required
def callback(request):
    try:
        token = oauth.auth0.authorize_access_token(request)
    except OAuthError as e:
        sentry_sdk.capture_exception(e)
        return redirect(reverse("login-fail"))
    userinfo = token["userinfo"]
    # with the email connection we dont get much info back about the user.
    # the nickname field is used as the username to match Control Panel, could
    # change this to the email field since we are using the email connection
    user, _ = User.objects.get_or_create(
        username=userinfo["nickname"], defaults={"email": userinfo["email"]}
    )
    _login(request, user=user)
    return redirect(reverse("dashboards:index"))


def logout(request):
    _logout(request)
    params = urlencode(
        {
            "returnTo": request.build_absolute_uri(reverse("index")),
            "client_id": settings.AUTH0_CLIENT_ID,
        }
    )
    url = f"https://{settings.AUTH0_DOMAIN}/v2/logout"
    return redirect(f"{url}?{params}")


@login_not_required
def healthcheck(request):
    """
    Healthcheck view for the dashboard service.
    """
    return HttpResponse("OK")


@login_not_required
def login_fail(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboards:index"))
    return render(request, "login/login_fail.html")
