import time

import requests
from django.conf import settings


class ControlPanelApiClient:
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        self.base_url = settings.CONTROL_PANEL_API_URL

    def get_access_token(self):
        token_url = f"http://{settings.AUTH0_DOMAIN}/oauth/token"
        data = {
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
        Check if we shold get a new access token
        """
        if not all([self.access_token, self.token_expiry]):
            return True
        current_time = int(time.time()) + 300  # 5 minute buffer
        return self.token_expiry < current_time

    def ensure_valid_token(self):
        """
        Get a valid access token, refreshing only if necessary
        """
        if not self.token_expired():
            return self.access_token

        token_data = self.get_access_token()
        self.access_token = token_data["access_token"]
        self.token_expiry = time.time() + token_data["expires_in"]
        return self.access_token

    def make_request(self, endpoint, method="GET", **kwargs):
        """
        Make an authenticated request to the API
        """
        token = self.ensure_valid_token()

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        url = f"{self.base_url}{endpoint}"

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()


api_client = ControlPanelApiClient()
