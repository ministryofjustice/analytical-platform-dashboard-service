import sentry_sdk
from authlib.integrations.django_client import OAuth, OAuthError
from django.conf import settings
from django.contrib.auth import login as _login
from django.contrib.auth import logout as _logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode

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
    next_url = request.GET.get("next", None)
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        urlencode_next = urlencode({"next": next_url})
        redirect_uri = f"{redirect_uri}?{urlencode_next}"
    return oauth.auth0.authorize_redirect(request, redirect_uri)


def get_or_create_user_from_id_token(id_token):
    """
    Resolves or creates a User instance based on an Auth0 ID token.

    This function first attempts to find a user by their Auth0 user ID (`sub` claim),
    which is stored in the `auth0_id` field. If no match is found, it falls back to
    looking up the user by email and updates or creates a user record as needed.

    Fields such as `email`, and `external_provider_id` are updated if they
    differ from the values in the ID token.

    Auth0 currently acts as an authentication broker for our application, mediating
    identity from providers like Entra ID and email/password. The `sub` value is unique
    per user within Auth0 and is used as a stable identifier.

    IMPORTANT:
    If Auth0 is removed from our authentication stack in the future (e.g., if we
    authenticate directly with Entra or another provider), we must update this logic to:
      - Stop relying on `auth0_id` for lookups.
      - Re-evaluate how user identities are matched across providers.

    Parameters:
        id_token (dict): A decoded Auth0 ID token containing user claims.

    Returns:
        User: A Django User instance, either found or newly created.
    """
    sub = id_token.get("sub")
    email = id_token.get(
        "email",
    ).lower()

    _provider, external_id = sub.split("|", 1)
    try:
        user = User.objects.get(auth0_id=sub)
        # Check if any email needs to be updated
        if user.email != email:
            user.email = email
            user.save()
    except User.DoesNotExist:
        user, _created = User.objects.update_or_create(
            email=email,
            defaults={
                "auth0_id": sub,
                "external_provider_id": external_id,
            },
        )
    return user


@login_not_required
def callback(request):
    try:
        token = oauth.auth0.authorize_access_token(request)
    except OAuthError as e:
        sentry_sdk.capture_exception(e)
        return redirect(reverse("login-fail"))
    userinfo = token["userinfo"]

    user_id = userinfo.get("sub", "").split("|")[-1]
    if not user_id:
        sentry_sdk.capture_message("User ID not found in userinfo")
        return redirect(reverse("login-fail"))

    user = get_or_create_user_from_id_token(userinfo)
    _login(request, user=user)
    next_url = request.GET.get("next", None)
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    return redirect(settings.LOGIN_REDIRECT_URL)


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


def debug_404(request):
    """
    Example 404 view for the dashboard service.
    """
    return render(request, "404.html", status=404)


def debug_500(request):
    """
    Example 500 view for the dashboard service.
    """
    return render(request, "500.html", status=500)
