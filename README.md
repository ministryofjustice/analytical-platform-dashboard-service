# Analytical Platform Dashboard Service

 [![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/analytical-platform-dashboard-service/badge)](https://github-community.service.justice.gov.uk/repository-standards/analytical-platform-dashboard-service)

## Setup Instructions

### Prerequisites

You will need to install `uv`, you can do this with brew:

```sh
brew install uv
```

Or see the full installation instructions [here](https://docs.astral.sh/uv/getting-started/installation/).

### Database for local development

You will need postgresql installed and running, then create the database with:

```sh
createdb dashboard_service
```

### Developer setup

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
