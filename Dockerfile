FROM public.ecr.aws/ubuntu/ubuntu:24.04@sha256:e3b7fe80bcb7bd1b8c2301b8cf88973aa04774afdcf34d645897117dcbc0bc4a AS build


SHELL ["/bin/bash", "-e", "-u", "-o", "pipefail", "-c", "-x"]

ENV DEBIAN_FRONTEND=noninteractive

RUN <<EOF
apt-get update --quiet --yes
apt-get install --quiet --yes \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    "python3.12-dev=3.12.3-1ubuntu0.5" \
    "ca-certificates=20240203"
EOF

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - prevent uv from accidentally downloading isolated Python builds,
# - pick the Python interpreter,
# - and finally declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/bin/python3.12 \
    UV_PROJECT_ENVIRONMENT=/app

# Synchronize DEPENDENCIES without the application itself.
# This layer is cached until uv.lock or pyproject.toml change
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

##########################################################################

FROM public.ecr.aws/ubuntu/ubuntu:24.04@sha256:e3b7fe80bcb7bd1b8c2301b8cf88973aa04774afdcf34d645897117dcbc0bc4a AS runtime

LABEL org.opencontainers.image.vendor="Ministry of Justice" \
      org.opencontainers.image.authors="Analytical Platform (analytical-platform@digital.justice.gov.uk)" \
      org.opencontainers.image.title="Dashboard Service" \
      org.opencontainers.image.description="Dashboard Service image for Analytical Platform" \
      org.opencontainers.image.url="https://github.com/ministryofjustice/analytical-platform-dashboard-service"

SHELL ["sh", "-exc"]

# Add the application virtualenv to search path.
ENV PATH=/app/bin:$PATH

# Don't run your app as root.

ENV CONTAINER_USER="analyticalplatform" \
    CONTAINER_UID="1000" \
    CONTAINER_GROUP="analyticalplatform" \
    CONTAINER_GID="1000" \
    DEBIAN_FRONTEND="noninteractive" \
    APP_ROOT="/app"

RUN <<EOF
userdel --remove --force ubuntu

groupadd \
    --gid ${CONTAINER_GID} \
    ${CONTAINER_GROUP}

useradd \
    --uid ${CONTAINER_UID} \
    --gid ${CONTAINER_GROUP} \
    --create-home \
    --shell /bin/bash \
    ${CONTAINER_USER}
EOF


ENTRYPOINT ["/docker-entrypoint.sh"]

# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT

RUN <<EOF
apt-get update --quiet --yes
apt-get install --quiet --yes \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    "python3.12-dev=3.12.3-1ubuntu0.5" \
    "ca-certificates=20240203"
apt-get clean --yes
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

COPY docker-entrypoint.sh /

# Copy the pre-built `/app` directory to the runtime container
# and change the ownership to user app and group app in one step.
COPY --from=build --chown=${CONTAINER_USER}:${CONTAINER_GROUP} ${APP_ROOT} ${APP_ROOT}

COPY manage.py ${APP_ROOT}/manage.py
COPY dashboard_service ${APP_ROOT}/dashboard_service
COPY templates ${APP_ROOT}/templates
COPY tests ${APP_ROOT}/tests
COPY pyproject.toml ${APP_ROOT}/pyproject.toml

USER ${CONTAINER_USER}
WORKDIR ${APP_ROOT}

# Run a smoke tests
RUN <<EOF
python -V
python -Im site
python manage.py check --deploy
EOF
