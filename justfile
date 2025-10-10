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

# Build css
build-css:
    npm install
    rm -rf static/assets/fonts
    rm -rf static/assets/images
    rm -rf static/assets/css
    mkdir -p static/assets/fonts
    mkdir -p static/assets/images
    mkdir -p static/assets/css
    cp -R node_modules/govuk-frontend/dist/govuk/assets/fonts/. static/assets/fonts
    cp -R node_modules/govuk-frontend/dist/govuk/assets/images/. static/assets/images
    cp -R node_modules/@ministryofjustice/frontend/moj/assets/images/. static/assets/images
    npm run css

build-js:
    npm install
    rm -rf static/assets/js
    mkdir -p static/assets/js
    cp node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.js static/assets/js/govuk-frontend.min.js

build-static:
    rm -rf static/
    just build-css
    just build-js

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
    uv run python manage.py runserver 8001

# Delete the .venv and drop the DB
destroy:
    rm -rf .venv/
    dropdb --if-exists {{ db_name }}

test *ARGS:
    pytest . --failed-first --maxfail=5 {{ ARGS }}
