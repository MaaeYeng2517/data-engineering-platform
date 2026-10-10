# The unified image

`data-engineering-platform` is a **single Docker image** that carries every application component
of the platform. One pull, one tag, and a per-service `PLATFORM_ROLE` decides what the container
actually runs.

- **Dockerfile:** `docker/unified/Dockerfile`
- **Role dispatcher:** `docker/unified/entrypoint.sh`
- **Extra Python packages:** `docker/unified/requirements-tools.txt`

---

## 1. Why it exists

The repository previously built seven images from the same source tree:

| Image | Dockerfile | Built from |
|---|---|---|
| `data-engineering-platform-backend` | `backend/Dockerfile` | root |
| `data-engineering-platform-worker` | `backend/Dockerfile.worker` | root |
| `data-engineering-platform-scheduler` | `backend/Dockerfile.scheduler` | root |
| `data-engineering-platform-flower` | `backend/Dockerfile.worker` | root |
| `dataair/airflow` | `docker/airflow/Dockerfile` | root |
| `dataair/tools` | `docker/tools/Dockerfile` | root |
| `data-engineering-platform-frontend` | `frontend/Dockerfile` | `frontend/` |

Four of those install the *same* `requirements.txt` into *separate* 3.57 GB images. Airflow and
the toolbox each rebuild yet another Python environment. A server ends up pulling roughly 17 GB
of logical images to run what is functionally one application.

The unified image collapses that. The per-service Dockerfiles are still there and still work —
nothing about the existing `docker-compose.yml` changes — but a deployment that does not need
per-service image pinning can now use a single reference.

---

## 2. What is inside

```
python:3.11-slim-bookworm          base OS, Node 20 (NodeSource), build toolchain
├── /usr/local                     main Python environment
│     requirements.txt             the backend pins, installed first and authoritative
│     + requirements-tools.txt     JupyterLab, Great Expectations, DuckDB, Polars, Arrow, ruff
├── /opt/airflow-venv              apache-airflow 2.10.3 + providers, under Airflow's own
│                                  constraints file
├── /opt/dbt-venv                  dbt-core / dbt-postgres / dbt-duckdb 1.9.1
├── /opt/web                       compiled Next.js standalone server
└── /app                           backend, dags, dbt, quality, tests, docs, docker/
```

### Why three Python environments

Installing all three dependency sets into one interpreter resolves into a **silently broken**
environment rather than an install error:

| Package | Backend pin | Toolbox pin | Conflict |
|---|---|---|---|
| `opentelemetry-api` / `-sdk` | `1.21.0` | `1.29.0` | **Yes** |
| `opentelemetry-exporter-otlp-proto-http` | `1.21.0` | `1.29.0` | **Yes** |
| `boto3` | `1.34.0` | `1.35.36` | minor |
| `pandas` | `2.2.1` | `2.2.3` | patch |
| `requests` | `2.31.0` | `2.32.3` | patch |
| `sqlalchemy` | `2.0.25` | `2.0.36` | patch |

The OpenTelemetry one is not survivable: `opentelemetry-instrumentation-fastapi==0.42b0` requires
`opentelemetry-api==1.21.0` exactly, and the backend loads that instrumentation at import time.
Airflow adds a third, larger set of exact pins (`sqlalchemy`, `pydantic`, `attrs`), and dbt
conflicts with Airflow directly — which is why `docker/airflow/Dockerfile` already isolated dbt in
its own venv before this image existed.

The resolution: the **backend's** `requirements.txt` owns the main environment, Airflow keeps its
constraints in `/opt/airflow-venv`, and dbt keeps its pins in `/opt/dbt-venv`. The toolbox extras
that do not conflict live in `docker/unified/requirements-tools.txt`.

---

## 3. Roles

Set `PLATFORM_ROLE`, or pass the role as the first argument. The entrypoint `exec`s the matching
binary in the matching virtualenv.

| `PLATFORM_ROLE` | Runs | Replaces |
|---|---|---|
| `backend` *(default)* | `uvicorn backend.main:app` | `backend` |
| `worker` | `python -m backend.app.workers.celery_worker` | `worker` |
| `scheduler` | `python -m backend.app.workers.celery_beat` | `scheduler` |
| `flower` | `celery … flower` | `flower` |
| `airflow-webserver` | `airflow webserver` | `airflow-webserver` |
| `airflow-scheduler` | `airflow scheduler` | `airflow-scheduler` |
| `airflow-triggerer` | `airflow triggerer` | `airflow-triggerer` |
| `airflow-init` | `airflow db migrate` | `airflow-init` |
| `web` | `node server.js` (Next.js standalone) | `frontend` |
| `dbt` | `dbt` against `/app/dbt` | `dbt` |
| `jupyter` | `jupyter lab` on `/app/notebooks` | `python` |
| `great-expectations` | `great_expectations` | `great-expectations` |
| `test` | `pytest tests/ -v` | — |
| `lint` | `ruff check backend tests workers dags` | — |
| `shell` | `/bin/bash` | — |

Anything unrecognised runs verbatim, so the image still works as a plain tool runner:

```bash
docker run --rm -it data-engineering-platform:latest python -V
```

### Ports

| Port | Used by |
|---|---|
| 8000 | `backend` |
| 3000 | `web` |
| 8080 | `airflow-webserver` |
| 5555 | `flower` |
| 8888 | `jupyter` |

---

## 4. Build

```bash
docker build -f docker/unified/Dockerfile -t data-engineering-platform:latest .
```

Build args: `PYTHON_VERSION=3.11`, `NODE_VERSION=20`, `AIRFLOW_VERSION=2.10.3`,
`AIRFLOW_PYTHON_MINOR=3.11`, `DBT_VERSION=1.9.1`.

Layer caching is deliberate:

- dependencies are installed in their own layer, before any source is copied
- `web-deps` and `python-deps` are independent stages, so BuildKit compiles the
  Next.js bundle while pip is still working
- the runtime stage copies finished artefacts rather than rebuilding them

A source-only change reuses every cached layer. A `requirements.txt` change re-runs pip and
everything downstream.

---

## 5. Push

```bash
docker login                                   # sign in first
docker tag  data-engineering-platform:latest \
            maaeyeng2517/data-engineering-platform:latest
docker push   maaeyeng2517/data-engineering-platform:latest
```

To pull on a server:

```bash
docker pull maaeyeng2517/data-engineering-platform:latest
docker run -d --name dataair-backend \
  -e PLATFORM_ROLE=backend \
  -p 8000:8000 \
  --env-file .env \
  maaeyeng2517/data-engineering-platform:latest
```

---

## 6. Running the stack from one image

```yaml
services:
  backend:
    image: maaeyeng2517/data-engineering-platform:1.0.0
    environment:
      PLATFORM_ROLE: backend
    ports: ["8000:8000"]

  worker:
    image: maaeyeng2517/data-engineering-platform:1.0.0
    environment:
      PLATFORM_ROLE: worker
      CELERY_BROKER_URL: redis://redis:6379/0

  scheduler:
    image: maaeyeng2517/data-engineering-platform:1.0.0
    environment:
      PLATFORM_ROLE: scheduler
      CELERY_BROKER_URL: redis://redis:6379/0

  airflow-scheduler:
    image: maaeyeng2517/data-engineering-platform:1.0.0
    environment:
      PLATFORM_ROLE: airflow-scheduler
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+asyncpg://…@postgres:5432/airflow
      AIRFLOW__CELERY__RESULT_BACKEND: redis://redis:6379/0
```

Same image reference for every service; `PLATFORM_ROLE` is the only difference.

---

## 7. Environment variables

Everything the platform already reads, unchanged — `DATABASE_URL`, `REDIS_URL`, `ELASTICSEARCH_*`,
`MINIO_*`, `QDRANT_*`, `CELERY_BROKER_URL`, `JWT_SECRET_KEY`, `API_KEY_HMAC_SECRET`,
`PROFILE_SECRET_KEY`, `STRIPE_*`, `LLM_PROVIDER`, and so on. Two additions specific to this image:

| Variable | Default | Purpose |
|---|---|---|
| `PLATFORM_ROLE` | `backend` | Which component the container runs |
| `BACKEND_PORT` | `8000` | Listen port for the `backend` role |
| `JUPYTER_PORT` | `8888` | Listen port for the `jupyter` role |
| `FLOWER_PORT` | `5555` | Listen port for the `flower` role |

`PROFILE_SECRET_KEY` is worth calling out: it derives the Fernet key that encrypts service tokens
stored in the Profiles feature. **Rotating it makes every stored profile secret unreadable.**
It is required in production — `validate_production_config()` refuses to start without it.

---

## 8. Trade-offs

**Gains**

- One pull instead of seven; ~17 GB of logical images becomes one image
- One set of pins to audit, and the dependency conflicts are resolved in the build rather
  than at install time
- Every role ships the whole toolchain, so debugging a production container needs no extra image

**Costs**

- A larger image than a purpose-built one. `web` carries torch and Airflow it never uses.
- Roles share one filesystem, so a `test` or `shell` role can reach the API source and the
  Airflow home. Acceptable for a self-hosted platform; worth a decision before exposing it.
- The three virtualenvs must be kept in sync by hand. A new backend dependency does not appear
  in `/opt/airflow-venv`, and vice versa.
- `HEALTHCHECK` can only assert that the Python runtime imports; which role actually started
  has to be verified per service.

**Not a replacement for the per-service images.** They are still the better choice when image
size matters, when roles must be isolated, or when a build has to be reproducible per component.

---

## 9. Verifying the image

```bash
# every role resolves to a real binary
for role in backend worker scheduler flower dbt jupyter test lint; do
  docker run --rm data-engineering-platform:latest "$role" --help >/dev/null 2>&1 \
    && echo "ok  $role" || echo "FAIL $role"
done

# the three environments are genuinely separate
docker run --rm data-engineering-platform:latest shell -c \
  'python -c "import airflow" 2>/dev/null && echo "airflow leaked into main env" || echo "main env clean";
   /opt/airflow-venv/bin/python -c "import airflow; print(\"airflow\", airflow.__version__)"'
```

The repository `.dockerignore` is what keeps `.env`, `docker/prometheus/secrets/`, `*.password`
and `docker/ssl/` out of `COPY . .`. Without it the backend image ships real credentials — that
is exactly how `.env` ended up inside `data-engineering-platform-backend` before the file existed.