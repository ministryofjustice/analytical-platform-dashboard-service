from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # represents the full user_id stored in auth0
    auth0_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    # represents the external provider ID, e.g. the oid in EntraID.
    # This is parsed from the auth0_id
    external_provider_id = models.CharField(max_length=255, null=True, blank=True)
