from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.contrib.auth import login as _login
from django.contrib.auth import logout as _logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from dashboard_service.users.models import User

oauth = OAuth()
oauth.register(
    "auth0",
)


def login(request):
    redirect_uri = request.build_absolute_uri(reverse("callback"))
    return oauth.auth0.authorize_redirect(request, redirect_uri)


def callback(request):
    token = oauth.auth0.authorize_access_token(request)
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
            "returnTo": request.build_absolute_uri(reverse("dashboards:index")),
            "client_id": settings.AUTH0_CLIENT_ID,
        }
    )
    url = f"https://{settings.AUTH0_DOMAIN}/v2/logout"
    return redirect(f"{url}?{params}")
