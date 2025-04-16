import time
from typing import Any

import requests
from django.conf import settings


class ControlPanelApiClient:
    def __init__(self) -> None:
        self.access_token: str | None = None
        self.token_expiry: int | None = None
        self.base_url: str = settings.CONTROL_PANEL_API_URL

    def get_access_token(self) -> dict[str, Any]:
        """
        Request a new access token from Auth0

        Returns:
            Dict containing access_token and expires_in values
        """
        token_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
        data: dict[str, str] = {
            "client_id": settings.AUTH0_CLIENT_ID,
            "client_secret": settings.AUTH0_CLIENT_SECRET,
            "audience": settings.AUTH0_AUDIENCE,
            "grant_type": "client_credentials",
        }
        response = requests.post(url=token_url, data=data)
        response.raise_for_status()
        return response.json()

    def token_expired(self) -> bool:
        """
        Check if we should get a new access token

        Returns:
            True if token is expired or missing, False otherwise
        """
        if not all([self.access_token, self.token_expiry]):
            return True
        current_time = int(time.time()) + 300  # 5 minute buffer
        return self.token_expiry < current_time

    def ensure_valid_token(self) -> str:
        """
        Get a valid access token, refreshing only if necessary

        Returns:
            A valid access token
        """
        if not self.token_expired():
            return self.access_token

        token_data: dict[str, Any] = self.get_access_token()
        self.access_token = token_data["access_token"]
        self.token_expiry = int(time.time()) + token_data["expires_in"]
        return self.access_token

    def make_request(self, endpoint: str, method: str = "GET", **kwargs: Any) -> dict[str, Any]:
        """
        Make an authenticated request to the API

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments to pass to requests.request

        Returns:
            JSON response from the API
        """
        token: str = self.ensure_valid_token()

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        url = f"{self.base_url}{endpoint}"
        timeout = kwargs.pop("timeout", 3)

        response = requests.request(method, url, timeout=1, **kwargs)
        response.raise_for_status()
        return response.json()


api_client = ControlPanelApiClient()
