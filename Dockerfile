FROM public.ecr.aws/ubuntu/ubuntu:24.04@sha256:e3b7fe80bcb7bd1b8c2301b8cf88973aa04774afdcf34d645897117dcbc0bc4a as build

SHELL ["sh", "-exc"]

ENV DEBIAN_FRONTEND=noninteractive

RUN <<EOT
apt-get update --quiet --yes
apt-get install --quiet --yes \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3.12-dev \
    ca-certificates
EOT

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - prevent uv from accidentally downloading isolated Python builds,
# - and finally declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/bin/python3.12 \
    UV_PROJECT_ENVIRONMENT=/app


### End build prep -- this is where your app Dockerfile should start.

# Synchronize DEPENDENCIES without the application itself.
# This layer is cached until uv.lock or pyproject.toml change, which are
# only temporarily mounted into the build container since we don't need
# them in the production one.
# You can create `/app` using `uv venv` in a separate `RUN`
# step to have it cached, but with uv it's so fast, it's not worth
# it, so we let `uv sync` create it for us automagically.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

##########################################################################

FROM public.ecr.aws/ubuntu/ubuntu:24.04@sha256:e3b7fe80bcb7bd1b8c2301b8cf88973aa04774afdcf34d645897117dcbc0bc4a as runtime

SHELL ["sh", "-exc"]

# Add the application virtualenv to search path.
ENV PATH=/app/bin:$PATH

# Don't run your app as root.
RUN <<EOT
groupadd --system app
useradd --system --home-dir /app --gid app --no-user-group app
EOT

ENTRYPOINT ["/docker-entrypoint.sh"]

# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT

RUN <<EOT
apt-get update --quiet --yes
apt-get install --quiet --yes \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3.12 \
    ca-certificates
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

COPY docker-entrypoint.sh /

# Copy the pre-built `/app` directory to the runtime container
# and change the ownership to user app and group app in one step.
COPY --from=build --chown=app:app /app /app

COPY manage.py /app/manage.py
COPY dashboard_service /app/dashboard_service
COPY templates /app/templates
COPY tests /app/tests

USER app
WORKDIR /app

# Run a smoke tests
RUN <<EOT
python -V
python -Im site
python manage.py check --deploy
EOT
