from dashboard_service.users.models import User

AUTH0_AZURE_AD_PROVIDER = "waad"


def get_or_create_user_from_id_token(id_token):
    """
    Resolves or creates a User instance based on an Auth0 ID token.

    This function first attempts to find a user by their Auth0 user ID (`sub` claim),
    which is stored in the `auth0_id` field. If no match is found, it falls back to
    looking up the user by email and updates or creates a user record as needed.

    If a user is found by email and does not yet have an `auth0_id`, it is set.
    If the user already has an `auth0_id`, it is only updated if the new token comes
    from the Azure AD (`waad`) connection.

    Fields such as `email` and `external_provider_id` are updated if they differ from
    the values in the ID token.

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
    email = id_token.get("email", "").lower()

    if not sub or "|" not in sub:
        raise ValueError("Invalid or missing 'sub' claim in ID token")

    parts = sub.split("|")
    provider = parts[0]
    external_id = parts[-1]

    try:
        # First try to find user by auth0_id
        user = User.objects.get(auth0_id=sub)
        # Update email if it has changed
        if user.email != email:
            user.email = email
            user.save()
        return user
    except User.DoesNotExist:
        pass

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "auth0_id": sub,
            "external_provider_id": external_id,
        },
    )

    if created:
        return user

    if not user.auth0_id or provider == AUTH0_AZURE_AD_PROVIDER:
        user.auth0_id = sub
        user.external_provider_id = external_id
        user.save()

    return user
