# Unified image for the whole DataAir platform.
#
#   docker build -f docker/unified/Dockerfile -t data-engineering-platform:latest .
#
# One image carries the FastAPI backend, the Celery worker and beat, Airflow,
# dbt, the Jupyter toolbox and the compiled Next.js server. `docker/unified/
# entrypoint.sh` dispatches on PLATFORM_ROLE, so a deployment is one pull and
# one image reference with a per-service role instead of seven builds.
#
# Why the separate virtualenvs
# ----------------------------
# Airflow ships a large set of exact constraints (SQLAlchemy, pydantic,
# attrs, opentelemetry 1.27) that contradict the backend's pins, and dbt
# conflicts with Airflow directly. Installing all three into one environment
# resolves into a silently broken interpreter, so:
#
#   /usr/local        backend requirements.txt + the toolbox extras
#   /opt/airflow-venv apache-airflow 2.10.3 + providers, constrained
#   /opt/dbt-venv     dbt-core, isolated exactly as docker/airflow does it
#
# The entrypoint picks the right one per role.
ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG AIRFLOW_VERSION=2.10.3
ARG AIRFLOW_PYTHON_MINOR=3.11
ARG DBT_VERSION=1.9.1

# ---------------------------------------------------------------------------
# base: system packages plus Node, which the Next.js standalone server needs.
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ARG NODE_VERSION
ARG AIRFLOW_VERSION

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_VERSION=${NODE_VERSION} \
    AIRFLOW_HOME=/opt/airflow \
    AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags \
    AIRFLOW__CORE__PLUGINS_FOLDER=/opt/airflow/plugins \
    AIRFLOW__CORE__LOAD_EXAMPLES=false \
    DBT_PROFILES_DIR=/opt/airflow/dbt \
    WEB_HOME=/opt/web \
    APP_HOME=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      libssl-dev \
      libmagic1 \
      ca-certificates \
      gnupg \
      git \
      curl \
      unzip \
      make \
 && curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# A single unprivileged account owns the app, the Airflow home and the web build.
RUN groupadd -r dataair && useradd -r -g dataair -m -d /home/dataair dataair \
 && mkdir -p "${APP_HOME}" "${AIRFLOW_HOME}/dags" "${AIRFLOW_HOME}/logs" "${AIRFLOW_HOME}/plugins"

# The main Python environment lives in `base`, not in a child stage: layers
# added to a child stage are invisible to its parent, so installing here is what
# makes the runtime stage inherit site-packages. `runtime` is the only other
# stage built from `base`.
#
# requirements.txt is authoritative for anything it pins. The toolbox extras in
# requirements-tools.txt deliberately omit those pins so they cannot upgrade the
# OpenTelemetry 1.21 that opentelemetry-instrumentation-fastapi==0.42b0 requires.
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY docker/unified/requirements-tools.txt /tmp/requirements-tools.txt
RUN pip install -r /tmp/requirements-tools.txt

# ---------------------------------------------------------------------------
# python-deps: the environments that must stay separate.
# ---------------------------------------------------------------------------
FROM base AS python-deps

ARG AIRFLOW_VERSION
ARG AIRFLOW_PYTHON_MINOR
ARG DBT_VERSION

WORKDIR /app

# Airflow lives in its own venv. The apache/airflow base image ships a pip guard
# that refuses to run as root, so invoke pip as a module everywhere.
RUN python -m venv /opt/airflow-venv \
 && /opt/airflow-venv/bin/python -m pip install --no-cache-dir --upgrade pip \
 && /opt/airflow-venv/bin/python -m pip install --no-cache-dir \
      "apache-airflow==${AIRFLOW_VERSION}" \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${AIRFLOW_PYTHON_MINOR}.txt"

COPY docker/airflow/requirements.txt /tmp/requirements-airflow.txt
RUN /opt/airflow-venv/bin/python -m pip install --no-cache-dir \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${AIRFLOW_PYTHON_MINOR}.txt" \
      -r /tmp/requirements-airflow.txt

# dbt is isolated for the same reason it is in docker/airflow/Dockerfile: its
# pins do not survive inside Airflow's constrained environment.
RUN python -m venv /opt/dbt-venv \
 && /opt/dbt-venv/bin/python -m pip install --no-cache-dir --upgrade pip \
 && /opt/dbt-venv/bin/python -m pip install --no-cache-dir \
      "dbt-core==${DBT_VERSION}" \
      "dbt-postgres==${DBT_VERSION}" \
      "dbt-duckdb==${DBT_VERSION}"

# ---------------------------------------------------------------------------
# web-deps: compile the Next.js standalone server.
# ---------------------------------------------------------------------------
FROM node:${NODE_VERSION}-bookworm-slim AS web-deps

WORKDIR /src
ENV NEXT_TELEMETRY_DISABLED=1

# Dependencies in their own layer so a source-only change skips the install.
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# runtime: assemble the two trees.
# ---------------------------------------------------------------------------
FROM base AS runtime

ARG AIRFLOW_VERSION
ARG DBT_VERSION

# PYTHONPATH rather than WORKDIR so `import backend` resolves from any role,
# including the one that starts in /opt/web. The two venvs are deliberately NOT
# prepended to PATH: that would shadow the main interpreter and break every
# role that expects the backend's pins. The entrypoint calls their binaries by
# absolute path instead.
ENV PYTHONPATH=/app \
    AIRFLOW_VERSION=${AIRFLOW_VERSION} \
    DBT_VERSION=${DBT_VERSION}

COPY --from=python-deps /opt/airflow-venv /opt/airflow-venv
COPY --from=python-deps /opt/dbt-venv /opt/dbt-venv
COPY --from=web-deps /src/.next/standalone /opt/web
COPY --from=web-deps /src/.next/static /opt/web/.next/static
COPY --from=web-deps /src/public /opt/web/public

WORKDIR /app
# .dockerignore keeps .env, keys and local caches out of this context, so a
# `COPY . .` here cannot publish credentials.
COPY . .

RUN mkdir -p /app/logs /app/uploads /app/tmp \
 && cp -r /app/dags/. "${AIRFLOW_HOME}/dags/" \
 && install -m 0755 /app/docker/unified/entrypoint.sh /usr/local/bin/unified-entrypoint \
 && chown -R dataair:dataair /app /opt/airflow /opt/web "${AIRFLOW_HOME}"

USER dataair
WORKDIR /opt/web
EXPOSE 8000 3000

# The role decides what actually listens, so the health check only proves the
# runtime is alive, not that a given role started.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import backend.main" || exit 1

ENTRYPOINT ["/usr/local/bin/unified-entrypoint"]
CMD ["backend"]