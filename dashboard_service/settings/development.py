from .production import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS += ["dashboards.development.analytical-platform.service.justice.gov.uk"]  # noqa: F405

AUTH0_AUDIENCE = "urn:control-panel-dev-api"

CONTROL_PANEL_API_URL = (
    "https://controlpanel.services.dev.analytical-platform.service.justice.gov.uk/api/cpanel/v1/"
)
