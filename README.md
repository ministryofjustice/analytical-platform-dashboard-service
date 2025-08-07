# Analytical Platform Dashboard Service

[![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/analytical-platform-dashboard-service/badge)](https://github-community.service.justice.gov.uk/repository-standards/analytical-platform-dashboard-service)

## Setup Instructions

### Prerequisites

You will need to install `uv`, you can do this with brew:

```sh
brew install uv
```

Or see the full [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

### Database for local development

You will need PostgreSQL installed and running, then create the database with:

```sh
createdb dashboard_service
```

### Developer setup

#### .env file

You will need a `.env` file for local development - you can find this in 1Password, search for "Dashboard Service .env file for local development".

#### Using the justfile

Install `just` with brew, or an [alternative installation option](https://github.com/casey/just?tab=readme-ov-file#installation):

```sh
brew install just
```

You can then get setup for development with:

```sh
# installs the project, migrate the database, and
just develop
```

For further commands run `just` or check the `justfile`.

#### Install manually with uv

If you don't want to use the `justfile` you can install and run the project directly with `uv`:

1. Run `uv sync` from the root of the project. This will install the correct python version, create a `venv` and install dependencies.
1. You can then run commands with `uv run` e.g. `uv run python manage.py runserver`. Alternatively, source your venv as normal and run that way.

See the `uv` [docs](https://docs.astral.sh/uv/getting-started/) for further guidance.

### Pre-commit

Install pre-commit hooks with:

```sh
pre-commit install
```

### Running Alongside the Control Panel

The Dashboard Service is intentionally designed to know as little as possible about users and their access. All access to dashboards comes from the Control Panel API. As such, you will need to run the Control Panel alongside the Dashboard Service, otherwise you will encounter errors as soon as you log in.

You can set the URL of the Control Panel API using the `CONTROL_PANEL_API_URL` variable in your `.env` file.

## Authentication

Web applications for the dev and alpha Auth0 tenants are managed in code in the [Analytical Platform repository](https://github.com/ministryofjustice/analytical-platform/tree/main/terraform/auth0). They are configured to use passwordless authentication.

In addition, a client grant has been set up for each to allow machine-to-machine access with the Control Panel API.

To gain access to the Dashboard Service, a user must have the `access:dashboard` role. This role is granted to users when they are given access to a dashboard via the Control Panel. Email domains can also be whitelisted, so that any user with a valid email will be assigned the role upon their initial login to the Dashboard Service.

### Viewing Dashboards

Once a user has logged in to the Dashboard Service, they will only be able to view dashboards that either:

1. Have had access granted to them via the Control Panel, or
1. Have been whitelisted for all users with a specific email domain (e.g., all `@justice.gov.uk` users).
