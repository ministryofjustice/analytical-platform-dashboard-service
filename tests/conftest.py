from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_auth0():
    """Mock the auth0 object in the views module."""
    with patch("dashboard_service.views.oauth.auth0") as mock_auth0:
        yield mock_auth0
