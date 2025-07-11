from dashboard_service.users.models import User


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
