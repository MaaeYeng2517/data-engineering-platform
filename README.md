# DataAir — Knowledge Engineering Platform

A self-hosted data platform for ingesting documents, indexing them for hybrid retrieval, and
answering questions over your own knowledge. FastAPI backend, Next.js frontend, Airflow for
orchestration, dbt for transformations, and OpenMetadata for lineage.

## What it does

- **Ingestion** — connectors for the source types a deployment registers, with chunking and
  enrichment in `backend/app/services/indexing/`.
- **Knowledge bases** — publish indexed corpora and query them with hybrid (vector + keyword +
  graph) search.
- **RAG and chat** — an assistant on the same LLM gateway as the workspace (OpenAI, Anthropic,
  Gemini, or a local Ollama runtime). With no provider configured the gateway answers through a
  deterministic offline responder instead of failing.
- **Governance and evaluation** — roles, permissions, and retrieval quality measured against
  question sets drawn from your data.
- **Workflows and lineage** — repeatable pipelines, with dataset metadata registered in
  OpenMetadata.

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI, SQLAlchemy 2 (async), asyncpg |
| Web | Next.js 14 (App Router), TypeScript, Tailwind, shadcn/ui, Jest |
| Data | PostgreSQL 15, Redis, Qdrant, Elasticsearch, MinIO |
| Orchestration | Airflow (scheduler, triggerer, webserver), Celery workers, Flower |
| Transform | dbt |
| Catalog | OpenMetadata |
| Observability | Prometheus, Grafana, OpenTelemetry (OTLP traces) |

## Quick start

```bash
cp .env.example .env      # fill in what this machine needs
make up                   # start the whole stack
make health               # check backend, frontend, database, Redis, MinIO
```

The stack exposes the API on `http://localhost:8000` (OpenAPI at `/docs`), the frontend on
`http://localhost:3000`, Airflow on `http://localhost:8080`, Grafana on `http://localhost:3001`,
and OpenMetadata on `http://localhost:8585`.

## Database

The API creates its schema on startup through `backend.database.init_db()`. Point it at any
Postgres instance:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

Use `ssl=require` rather than `sslmode=require`: SQLAlchemy passes DSN query parameters to
`asyncpg.connect()` as keyword arguments, and asyncpg treats an unknown key as a Postgres runtime
setting — `sslmode=require` fails with *"parameter sslmode cannot be changed now"*. The verbatim
provider strings stay available as `POSTGRES_URL` and `PRISMA_DATABASE_URL` for tooling that
speaks libpq (psql, Prisma CLI, dbt).

## Tests

```bash
make test            # both suites
make test-backend    # pytest, inside the backend container
make test-frontend   # jest, on the host
make lint            # ruff + next lint
make typecheck       # tsc --noEmit
```

The backend suite pins `LLM_PROVIDER` to the offline responder so no test ever calls a real model.
Frontend tests run on the host because the production image mounts an empty `node_modules`
volume and ships no jest binary.

## Deployment

**Frontend → Vercel.** Point the build at the deployed API, then deploy from `frontend/`:

```bash
vercel env add NEXT_PUBLIC_API_URL production   # https://<api-host>/api/v1
vercel --prod
```

Without this variable the bundle falls back to `http://localhost:8000/api/v1` and every request
fails in the visitor's browser with `Failed to fetch`; the chat client reports that as
"the chat service is not available right now".

**Backend → FastAPI Cloud.** `pyproject.toml` declares the dependency set and
`[tool.fastapi] entrypoint = "backend.main:app"`, and `.fastapicloudignore` keeps the upload to
the API alone:

```bash
export FASTAPI_CLOUD_TOKEN=...        # deploy token
fastapi deploy --app-id <app-id>
```

The ML stack (torch, transformers, sentence-transformers) is intentionally absent from
`pyproject.toml`: nothing imports it at startup, and pulling it in would dominate the build.
Endpoints that need embeddings will fail until those dependencies are added and the app redeployed.

At least one `DATABASE_URL` must be set on the app, otherwise the lifespan's `init_db()` fails and
the deployment cannot verify. Env vars are managed with a signed-in session, not a deploy token:

```bash
fastapi cloud login
fastapi cloud env set --secret DATABASE_URL 'postgresql+asyncpg://…?ssl=require'
```

## Layout

```
backend/          FastAPI app: api routers, models, services, workers
frontend/         Next.js app: marketing site, dashboard, chat widget
dags/             Airflow DAGs
dbt/              dbt models and transformations
quality/          data quality checks
config/           Airflow configuration
docker/           images and init SQL
tests/            pytest suite
```

## Conventions

- Backend formatting and linting via `ruff` (`ruff.toml`); frontend via `next lint`.
- Secrets live in `.env`, which is gitignored. Only `.env.example` is committed.
- Generated output (`logs/`, `data/`, `.next/`, `node_modules/`) stays out of git.

## License

Apache License 2.0 — see [LICENSE](LICENSE).