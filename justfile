set dotenv-load

db_name := "${DB_NAME:-dashboard_service}"

alias dev := develop
alias l := lint
alias run := runserver
alias m := migrate
alias mm:= makemigrations

@default:
    just -f justfile --list

# Install with uv, create pre-commit hooks and build static
install:
    uv sync
    uv run pre-commit install
    just build-static

# Install dependencies, migrate the database and run the server
develop: install
    just migrate
    just runserver

# Build static. TODO add the build steps!
build-static:
    mkdir -p static

# Lint and format with ruff
lint:
    ruff check --fix
    ruff format

# Check for migration changes
makemigrations *ARGS:
    uv run python manage.py makemigrations {{ ARGS }}

# Migrate the database
migrate *ARGS:
    uv run python manage.py migrate {{ ARGS }}

# Run the django server
runserver:
    uv run python manage.py runserver

# Delete the .venv and drop the DB
destroy:
    rm -rf .venv/
    dropdb --if-exists {{ db_name }}
