from unittest.mock import patch

import pytest

from dashboard_service.dashboards.api import api_client as _api_client


@pytest.fixture(autouse=True)
def mock_requests():
    """
    Make sure the requests library is always mocked.
    """
    with patch("dashboard_service.dashboards.api.requests") as mock_requests:
        yield mock_requests


@pytest.fixture()
def api_client():
    """
    Fixture to reset the API client before each test.
    """
    _api_client.access_token = None
    _api_client.token_expiry = None
    yield _api_client
