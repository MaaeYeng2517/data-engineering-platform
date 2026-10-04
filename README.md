# DataAir — Knowledge Engineering Platform

A self-hosted platform for turning documents into a searchable, citable knowledge base.
Upload files, let the platform chunk and embed them, then ask questions and get answers with
citations back to the source passages.

The stack is a FastAPI backend, a Next.js frontend, Airflow for orchestration, dbt for warehouse
transformations, Great Expectations for data quality, and OpenMetadata for lineage.

---

## Table of contents

1. [How the system fits together](#1-how-the-system-fits-together)
2. [The five things a user does](#2-the-five-things-a-user-does)
3. [Accounts, workspaces and access](#3-accounts-workspaces-and-access)
4. [What happens to a request](#4-what-happens-to-a-request)
5. [From document to searchable chunks](#5-from-document-to-searchable-chunks)
6. [How search works](#6-how-search-works)
7. [How RAG builds an answer](#7-how-rag-builds-an-answer)
8. [The chat assistant and its LLM gateway](#8-the-chat-assistant-and-its-llm-gateway)
9. [Background pipelines](#9-background-pipelines)
10. [The frontend](#10-the-frontend)
11. [Observability](#11-observability)
12. [Running it locally](#12-running-it-locally)
13. [Configuration](#13-configuration)
14. [Tests](#14-tests)
15. [Deployment](#15-deployment)
16. [Implementation status — read this before planning work](#16-implementation-status--read-this-before-planning-work)
17. [Repository layout](#17-repository-layout)
18. [License](#18-license)

---

## 1. How the system fits together

Two groups of services. The **application group** answers user requests. The **pipeline group**
prepares data that the application then serves.

```mermaid
flowchart LR
    subgraph client["Browser / client"]
        UI["Next.js app<br/>dashboard, marketing, chat"]
    end

    subgraph edge["Edge"]
        NG["nginx<br/>:80"]
    end

    subgraph app["Application"]
        BE["backend<br/>FastAPI :8000"]
        FE["frontend<br/>Next.js :3000"]
        WK["worker<br/>Celery"]
        BT["scheduler<br/>Celery beat"]
    end

    subgraph data["Data stores"]
        PG[("PostgreSQL<br/>app + warehouse")]
        RD[("Redis<br/>broker, cache")]
        S3[("MinIO<br/>object storage")]
        QD[("Qdrant")]
        ES[("Elasticsearch")]
    end

    subgraph pipeline["Pipeline"]
        AF["Airflow<br/>scheduler, webserver, triggerer"]
        DBT["dbt"]
        GE["Great Expectations"]
        OM["OpenMetadata<br/>catalog + lineage"]
    end

    subgraph obs["Observability"]
        PR["Prometheus"]
        GR["Grafana"]
    end

    UI --> NG
    NG --> FE
    NG --> BE
    BE --> PG
    BE --> RD
    BE --> S3
    BE --> QD
    BE --> ES
    BE -->|dispatch| WK
    BT --> WK
    S3 --> AF
    AF --> DBT
    AF --> GE
    AF --> PG
    DBT --> PG
    GE --> PG
    AF --> OM
    OM --> PG
    BE -->|reads warehouse + catalog| PG
    BE -->|reads catalog| OM
    PR --> BE
    GR --> PR
```

The most important structural fact: **the backend is the only service the browser talks to.**
Everything else — Airflow triggering, dbt, quality checks, catalog reads — is either initiated by
the backend or runs on a schedule and writes to Postgres, which the backend then reads.

| Address | Service |
|---|---|
| `http://localhost` | nginx — single entry point |
| `http://localhost:3000` | Next.js frontend (direct) |
| `http://localhost:8000` | FastAPI backend, OpenAPI at `/docs` |
| `http://localhost:8080` | Airflow |
| `http://localhost:3001` | Grafana |
| `http://localhost:8585` | OpenMetadata |

---

## 2. The five things a user does

### 2.1 Sign up — a new account creates its own workspace

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as FastAPI /auth/register
    participant D as PostgreSQL

    U->>A: POST /auth/register (email, password)
    A->>A: bcrypt hash the password
    A->>D: INSERT tenant ("<name>'s workspace", slug)
    A->>D: INSERT user (role = ADMIN if in ADMIN_EMAILS)
    A->>D: INSERT membership_plans (free, pro, enterprise)
    A->>D: INSERT subscription (free plan, active)
    A-->>U: access + refresh + CSRF cookies
    U->>A: GET /tenants/ (now authenticated)
    A-->>U: the workspace it just created
```

A tenant is the isolation boundary: users, knowledge bases, documents, API keys, work groups and
billing all hang off it.

### 2.2 Create a knowledge base and upload a document

```mermaid
flowchart TD
    A["User creates a knowledge base"] --> B["POST /knowledge-bases/"]
    B --> C["User uploads a file"]
    C --> D["POST /documents/upload<br/>multipart, session cookie + CSRF header"]
    D --> E["Read bytes, decode as UTF-8"]
    E --> F["processing_engine.process()"]
    F --> F1["TextExtractor.extract()"]
    F --> F2["clean() + normalize()"]
    F --> F3["Chunker.chunk()<br/>800 chars, 100 overlap"]
    F --> F4["EntityExtractor.extract()<br/>first 1000 chars"]
    F1 & F2 & F3 & F4 --> G["Store content, chunks, entities"]
    G --> H["status = processed"]
    H --> I["Visible in the dashboard"]
```

### 2.3 Index — chunk, embed, and register for search

```mermaid
flowchart LR
    A["document content"] --> B["TokenChunker<br/>300 tokens, 50 overlap<br/>chunk_id = doc:index"]
    B --> C["EmbeddingService.embed()"]
    C --> C1{"OPENAI_API_KEY set?"}
    C1 -->|yes| C2["OpenAI embeddings API<br/>1536 / 3072 dims"]
    C1 -->|no| C3["Offline hashing trick<br/>384 dims, deterministic"]
    C2 --> D[(VectorIndex)]
    C3 --> D
    B --> E[(KeywordIndex)]
    B --> F[(MetadataIndex)]
    D --> G[HybridIndex]
    E --> G
    F --> G
```

Embeddings are cached in an LRU of 2048 entries keyed by `model:text`, so re-indexing the same
text costs nothing. Without an OpenAI key the embedder falls back to a signed hashing-trick
bag-of-words: not semantic, but deterministic and offline, which keeps the pipeline testable.

### 2.4 Search — ask the index a question

```mermaid
flowchart TD
    A["POST /search/ with query + limit"] --> B["RetrievalEngine.search()"]
    B --> C["Over-fetch: limit × 2 candidates"]
    C --> D["KeywordIndex: term frequency score"]
    C --> E["VectorIndex: cosine similarity<br/>numpy over every embedding"]
    D --> F["Merge by document id"]
    E --> F
    F --> G["hybrid_score = 0.4·keyword + 0.6·vector"]
    G --> H["MetadataIndex filter: exact match on every key"]
    H --> I["Reranker"]
    I --> I1["0.5·hybrid + 0.3·lexical overlap + 0.1·position + 0.1·length"]
    I1 --> J["Return results, total, latency_ms"]
```

### 2.5 Ask a question — RAG and chat

```mermaid
flowchart TD
    Q["User question"] --> S["RetrievalEngine.search()<br/>top passages"]
    S --> B["ContextBuilder.build()"]
    B --> B1["Deduplicate by chunk, then document"]
    B1 --> B2["Drop low-relevance passages"]
    B2 --> B3["Compress each passage to 500 chars"]
    B3 --> B4["Order by relevance"]
    B4 --> B5["Apply budget: 4000 tokens cumulative"]
    B5 --> P["Numbered passages [1] [2] …<br/>+ instruction: answer only from these, cite them"]
    P --> L["LLMGateway.generate()"]
    L --> L1{"Provider answered?"}
    L1 -->|yes| A["Answer + citations + token usage"]
    L1 -->|no| X["Extractive fallback:<br/>quote the passages verbatim"]
    A --> U["UI shows the answer with sources"]
```

---

## 3. Accounts, workspaces and access

```mermaid
flowchart LR
    R["Role on the user<br/>GUEST · MEMBER · ADMIN"] --> G1["require_platform_user<br/>blocks disabled users and tenants"]
    R --> G2["require_admin<br/>admin router only"]
    R --> G3["GovernanceEngine catalogue<br/>READ WRITE DELETE ADMIN PUBLISH APPROVE"]

    T["Tenant id on the row"] --> S1["work groups<br/>404 for other tenants' ids"]
    T --> S2["profiles<br/>every query filtered by tenant_id"]
    T --> S3["API keys<br/>filtered by user_id"]
    T --> S4["documents, knowledge bases,<br/>workflows, metadata"]

    K["Session cookie<br/>dataair_access_token"] --> U["get_current_user"]
    B["Bearer token"] --> U
    U --> U1["Reload user + tenant from Postgres"]
    U1 --> U2["401 unauthenticated · 403 disabled"]
```

Tokens are JWTs signed with `JWT_SECRET_KEY`, carrying `user_id`, `tenant_id`, `email`, `role`.
The access token lives 24 hours, the refresh token 30 days, and refresh rotates both plus the CSRF
cookie. Passwords are bcrypt.

API keys are `dk_`-prefixed. Only a 12-character prefix and an HMAC-SHA256 hash are stored — the
plaintext is returned exactly once. See
[the status section](#16-implementation-status--read-this-before-planning-work) for what is not
wired up yet.

---

## 4. What happens to a request

Three layers wrap every route. Starlette runs the most recently added middleware outermost, so the
effective inbound order is:

```mermaid
flowchart TD
    R["Incoming request"] --> CSRF["CSRF guard"]
    CSRF --> OTEL["OpenTelemetry span<br/>(only if OTEL_EXPORTER_OTLP_ENDPOINT is set)"]
    OTEL --> CORS["CORS<br/>allow_credentials, explicit origins"]
    CORS --> ROUTER["Router + dependency"]
    ROUTER --> RESP["Response"]
    CSRF -.->|"POST/PUT/PATCH/DELETE, cookie caller,<br/>no CSRF token"| X["403"]
    CSRF -.->|"exempt: /auth/*, /chat, /contact,<br/>billing/webhook, or x-api-key / Bearer"| ROUTER
```

The CSRF scheme is a double-submit cookie: the token is readable by JavaScript, echoed back in the
`x-csrf-token` header, and compared with `hmac.compare_digest`. The frontend's axios interceptor
fetches the cookie once per session and attaches it to every mutating request, so plain `fetch`
calls (including the chat stream) cannot mutate state without going through that client.

Rate limiting exists on exactly one endpoint: `/chat`, a sliding window of 20 requests per 60
seconds keyed by user id or IP, tracked in process.

---

## 5. From document to searchable chunks

Two chunkers exist, on purpose:

| | `TokenChunker` (`services/chunking.py`) | `Chunker` (`services/processing`) |
|---|---|---|
| Used by | the indexing task | the upload endpoint |
| Granularity | 300 tokens, 50 overlap | 800 characters, 100 overlap |
| Chunk identity | `f"{document_id}:{index}"` — stable across re-indexing | positional only |
| Carries | `start_char`, `end_char`, `token_count` | raw text |

```mermaid
flowchart LR
    subgraph upload["Upload path — reachable from the UI"]
        A1["bytes"] --> A2["decode utf-8, errors ignored"] --> A3["extract · clean · normalize"] --> A4["800/100 character chunks"] --> A5["entities from first 1000 chars"]
    end
    subgraph index["Indexing path — Celery task dataair.index.document"]
        B1["content"] --> B2["300/50 token chunks"] --> B3["embed all chunks"] --> B4["vector + keyword + metadata indexes"]
    end
    A5 -.->|"chunks are stored,<br/>not indexed"| GAP(( ))
    B4 --> SEARCH["RetrievalEngine"]
```

This split is the single biggest thing to know about the codebase: **the upload path stores
chunks, the indexing path embeds them, and nothing connects the two yet.** Section 16 spells out
the consequence.

---

## 6. How search works

```mermaid
flowchart TD
    Q["query"] --> K["KeywordIndex<br/>per term: 1 / (1 + occurrences)"]
    Q --> V["VectorIndex<br/>cosine similarity, numpy"]
    K --> M["Merge into one score per document"]
    V --> M
    M --> H["0.4 × keyword + 0.6 × vector"]
    H --> F["Metadata filter<br/>exact match on every filter key"]
    F --> R["Rerank"]
    R --> R1["0.5 × hybrid"]
    R --> R1b["0.3 × query-term overlap"]
    R --> R1c["0.1 × position bonus"]
    R --> R1d["0.1 × length score"]
    R1 & R1b & R1c & R1d --> OUT["top_k results"]

    G["GraphIndex<br/>substring match on entity name"] -.->|"only /search/graph"| OUT2["graph results"]
```

Four endpoints, not one parameterised route:

| Endpoint | Handler |
|---|---|
| `POST /api/v1/search/` | hybrid search, `search_type` in the body |
| `POST /api/v1/search/keyword` | keyword only (query params) |
| `POST /api/v1/search/vector` | vector only (query params) |
| `POST /api/v1/search/graph` | graph only (query params) |

`kb_ids` and `score_threshold` are accepted by the schema but not applied by the retrieval engine.
The graph index is only reachable through `/search/graph`.

---

## 7. How RAG builds an answer

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as POST /rag/
    participant R as RetrievalEngine
    participant C as ContextBuilder
    participant G as LLMGateway
    participant P as Provider

    U->>A: {query, kb_ids}
    A->>R: search(query, kb_ids, limit)
    R-->>A: ranked passages
    A->>C: build(query, passages)
    Note over C: dedupe → filter → compress (500 chars)<br/>→ order → 4000-token budget
    C-->>A: context, sources, total_tokens
    A->>G: generate(messages, system=passages, temp, max_tokens)
    G->>P: first available provider
    alt provider answered
        P-->>G: text + usage
        G-->>A: answer
    else provider failed or returned nothing
        G-->>A: degraded
        A->>A: extractive fallback — quote passages verbatim
    end
    A-->>U: answer, sources, citations, latency_ms, token_usage
```

Two details worth knowing. The context budget counts **whitespace-separated words**, not tokens,
so it is an approximation. And retrieval failures are swallowed: a broken index yields an
extractive answer rather than a 500.

---

## 8. The chat assistant and its LLM gateway

The chat endpoint is public — the marketing page uses it before anyone signs in — so it is
rate limited per caller and grounded defensively.

```mermaid
flowchart TD
    Q["Question + conversation history"] --> RL{"Rate limit<br/>20 req / 60 s per user or IP"}
    RL -->|over| E429["429 Too many requests"]
    RL -->|ok| G["_grounded_context()<br/>top 5 passages, ≤ 6000 chars, labelled [1] [2] …"]
    G --> GATE["LLMGateway chain resolution"]
    GATE --> P1["openai"] --> P2["anthropic"] --> P3["google"] --> P4["ollama"] --> P5["offline"]
    GATE -.->|"LLM_PROVIDER is set and available"| PIN["pinned provider first"]
    P1 & P2 & P3 & P4 --> OK{"Answer non-empty?"}
    OK -->|yes| SSE["SSE stream"]
    OK -->|no| NEXT["try next provider"]
    NEXT --> P5
    P5 --> SSE
    SSE --> S1["event: meta — provider, model, degraded"]
    SSE --> S2["event: delta — text chunks"]
    SSE --> S3["event: done — latency, token usage, sources"]
    SSE --> S4["event: error — detail, truncated"]
```

The chain is walked in order. If a provider fails **before** any token is emitted, the gateway
moves to the next one; if it fails mid-stream, the error propagates rather than swapping
providers under a partially delivered answer. With no provider configured, the offline responder
answers "Sorry, I'm not service" and names the environment variables that would enable a real
model — which is also what the test suite pins, so no test ever calls a paid model.

The frontend streams with raw `fetch`, not axios, because axios cannot stream a response body in
the browser and the CSRF client would buffer it. Aborts stay aborts; any other transport failure
becomes "Sorry, the chat service is not available right now" instead of the browser's raw
`Failed to fetch`.

---

## 9. Background pipelines

```mermaid
flowchart LR
    subgraph minio["MinIO bucket"]
        F["CSV / files"]
    end

    F -->|"*/30 * * * *"| D1["ingest_minio_landing"]
    D1 --> RAW[("raw.sales<br/>raw.products<br/>raw.customers")]
    RAW --> D2["warehouse_build · 02:00<br/>dbt clean → deps → build"]
    D2 --> STG[("staging.stg_sales<br/>staging.stg_products<br/>views")]
    STG --> MART[("marts.sales_daily<br/>incremental delete+insert")]
    MART --> D3["data_quality_check · 03:30<br/>Great Expectations suite"]
    D3 --> AUDIT[("audit.data_quality_results<br/>audit.elt_runs")]
    D1 --> AUDIT
    D2 --> AUDIT
    D3 -->|"fail → raise"| FAIL["DAG fails the run"]
    MART --> OM["OpenMetadata<br/>lineage + glossary"]
    D4["catalog_sync · 04:00"] -.->|"reachability + freshness only"| OM

    AUDIT --> BE["backend reads<br/>/api/v1/warehouse/*"]
    OM --> BE
    BE --> UI["Warehouse · Lineage · Monitoring pages"]
```

Airflow never calls the API and never uses Celery — it shares only Postgres. The join is
one-directional: **Airflow writes, the backend reads.** The backend can also trigger and pause DAGs
(`POST /api/v1/pipelines/dags/{dag_id}/trigger`), but no DAG ever calls back into the backend.

Celery runs three queues — `default`, `indexing`, `ingestion` — with tasks for chunking+embedding
(`dataair.index.document`), searching the index (`dataair.index.query`), embedding batches
(`dataair.index.embed`), and ingestion. Beat schedules a tenant-refresh task every 15 minutes.
Flower gives a web view of the queue.

---

## 10. The frontend

Next.js 14 App Router, TypeScript, Tailwind, shadcn/ui, TanStack Query, Recharts and React Flow.

```mermaid
flowchart TD
    L["app/layout.tsx<br/>providers + theme"] --> M["app/page.tsx<br/>marketing + chat widget"]
    L --> AUTH["login · register"]
    L --> DASH["(dashboard)/*<br/>16 sections"]
    DASH --> S1["search · rag · knowledge · documents"]
    DASH --> S2["pipelines · workflows · stacks · tools"]
    DASH --> S3["governance · audit · team · billing"]
    DASH --> S4["profiles · configuration · settings"]
    S1 --> C1["lib/api/data.ts<br/>normalises responses to {items,total}"]
    S2 --> C1
    S3 --> C1
    S4 --> C1
    C1 --> C2["lib/api/client.ts<br/>axios + CSRF interceptor"]
    C2 --> C3["lib/api/chat.ts<br/>SSE stream via fetch"]
    C2 --> API["FastAPI /api/v1/*"]
    C3 --> API
```

How state and errors flow:

- `ApiClient` sets `baseURL` from `NEXT_PUBLIC_API_URL`, sends cookies, and attaches
  `x-csrf-token` to every mutating request — fetching the token from the cookie, or from
  `GET /auth/csrf-token` on a cold visit.
- A **401** redirects to `/login?next=<path>`, except on `/auth/*` and the login/register pages,
  so an anonymous visitor on the marketing page is never trapped behind the login form.
- Response shapes are normalised in one place: a bare array, a wrapped object, or a single
  resource all become `{items, total}`.
- `next.config.js` adds five security headers, a `/api/backend/*` rewrite for same-origin calls,
  and standalone output for the Docker image.

---

## 11. Observability

```mermaid
flowchart LR
    BE["backend"] -->|"traces (OTLP/HTTP)"| OTEL["OTLP endpoint"]
    OTEL --> GR1["Grafana Cloud"]
    BE -->|"/metrics"| PR["Prometheus<br/>:9090"]
    WK["Celery worker"] -->|"metrics :9100"| PR
    PR --> GR["Grafana<br/>dashboards + alert rules"]
    BE -->|"OTLP traces"| GR
```

Tracing is opt-in: with no `OTEL_EXPORTER_OTLP_ENDPOINT` the app adds no instrumentation at all,
so local runs stay quiet. Instrumentation covers the app, outgoing HTTP, and SQLAlchemy — the
last one against the sync engine, because the OpenTelemetry SQLAlchemy instrumentation of that
version rejects an `AsyncEngine`.

`GET /metrics` exposes Prometheus metrics; the worker and beat expose theirs on `:9100`.

---

## 12. Running it locally

```bash
cp .env.example .env      # fill in only what this machine needs
make up                   # start the whole stack
make health               # backend, frontend, database, Redis, MinIO
make logs                 # tail everything
make down                 # stop and remove volumes
```

Useful targets:

| Target | What it does |
|---|---|
| `make test` | backend and frontend suites |
| `make test-backend` | pytest inside the backend container |
| `make test-frontend` | jest on the host |
| `make lint` | ruff + next lint |
| `make typecheck` | `tsc --noEmit` |
| `make migrate` | `alembic upgrade head` inside the container |
| `make restart` / `make build` / `make clean` | container lifecycle |

---

## 13. Configuration

Everything is environment variables, read once in `backend/config.py`. `.env` is gitignored;
only `.env.example` is committed.

The groups that matter:

| Group | Variables |
|---|---|
| Database | `DATABASE_URL`, `DATABASE_POOL_SIZE`, `DATABASE_ECHO` |
| Auth | `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `CSRF_SECRET_KEY`, `API_KEY_HMAC_SECRET`, `ADMIN_EMAILS`, `COOKIE_SECURE`, `COOKIE_SAMESITE` |
| LLM | `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `LLM_OFFLINE_FALLBACK` |
| Chat | `CHAT_RATE_LIMIT_REQUESTS`, `CHAT_RATE_LIMIT_WINDOW_SECONDS`, `CHAT_SYSTEM_PROMPT`, `CHAT_TEMPERATURE`, `CHAT_MAX_TOKENS`, `CHAT_MAX_CONTEXT_CHARS` |
| Billing | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SAAS_PLANS` |
| Platform | `MINIO_*`, `QDRANT_URL`, `ELASTICSEARCH_URL`, `AIRFLOW_*`, `OPENMETADATA_*`, `ALLOWED_ORIGINS` |
| Telemetry | `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_TRACES_SAMPLER_ARG` |

### Connecting to Postgres

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

Use `ssl=require`, not `sslmode=require`. SQLAlchemy hands DSN query parameters to
`asyncpg.connect()` as keyword arguments, and asyncpg treats an unrecognised key as a Postgres
runtime setting — so `sslmode=require` fails at startup with
*"parameter sslmode cannot be changed now"*. Keep the provider's own string around as
`POSTGRES_URL` for psql, the Prisma CLI, or dbt.

The schema is created at startup by `backend.database.init_db()`.

### Production gate

When `APP_ENV=production`, `validate_production_config()` refuses to start unless
`JWT_SECRET_KEY`, `CSRF_SECRET_KEY`, `API_KEY_HMAC_SECRET`, `PROFILE_SECRET_KEY`,
`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` are set to real values, `COOKIE_SECURE=true`,
`ADMIN_EMAILS` is non-empty, and no CORS origin is `*`. All problems are reported in one error
rather than one at a time.

---

## 14. Tests

```bash
make test            # both suites
make test-backend    # 73 tests, inside the container
make test-frontend   # 21 tests, on the host
```

- An autouse fixture pins `LLM_PROVIDER` to the offline responder, so the suite never calls a real
  model and never depends on a key being present.
- Backend coverage: app lifespan and plan seeding, health endpoint in both states, CSRF exemption
  and bypass rules, public route registration, tenant-scoped profiles, LLM gateway fallback,
  streaming frame parsing.
- Frontend tests run on the **host**: the production image mounts an empty `node_modules` volume
  and ships no jest binary.
- The chat client has explicit tests for the three interesting cases — a rejected request, an
  abort, and a stream that drops mid-answer.

---

## 15. Deployment

### Frontend → Vercel

```bash
cd frontend
vercel env add NEXT_PUBLIC_API_URL production   # https://<api-host>/api/v1
vercel --prod
```

Without that variable the bundle falls back to `http://localhost:8000/api/v1`, which resolves in
the *visitor's* browser, so every request fails. Set it before the first deploy.

### Backend → FastAPI Cloud

`pyproject.toml` declares the dependency set and the entrypoint; `.fastapicloudignore` keeps the
upload to the API alone (no frontend, tests, docs, logs).

```bash
export FASTAPI_CLOUD_TOKEN=...
fastapi deploy --app-id <app-id>
```

Two deliberate choices:

- The ML stack (torch, transformers, sentence-transformers) is **not** in `pyproject.toml`.
  Nothing imports it at startup, and pulling it in would dominate the build. Endpoints that need
  real embeddings need those dependencies added first.
- At least one `DATABASE_URL` must exist on the app, or the lifespan's `init_db()` fails and the
  deployment cannot verify. Env vars need a signed-in session, not a deploy token:

```bash
fastapi cloud login
fastapi cloud env set --secret DATABASE_URL 'postgresql+asyncpg://…?ssl=require'
```

---

## 16. Implementation status — read this before planning work

The identity, billing, work-group and profile halves are persisted and wired end to end. The
knowledge-pipeline half is not, and the difference is easy to miss from the API surface.

| Area | State |
|---|---|
| Tenants, users, sessions, CSRF, admin, work groups, profiles, billing, API keys | Backed by Postgres and the SQLAlchemy models |
| `tenants`, `knowledge-bases`, `documents`, `workflows`, `metadata` routers | Module-level in-memory dicts, scoped by `tenant_id` for the process lifetime |
| `chunks`, `entities`, `relationships`, `sources`, `evaluation_*`, `metadata_schemas` tables | Declared in the models, never written by any code path |
| Indexing | `dataair.index.document` chunks, embeds and indexes — and nothing dispatches it |
| Cross-process visibility | `hybrid_index` is a per-process singleton, and the API and worker are separate containers, so a worker-side index is invisible to the API |
| `POST /documents/upload` | Extracts, chunks and stores — but never indexes, so uploaded documents cannot be searched or grounded |
| Qdrant, Elasticsearch | Health-probed only; never written. Vector search is a linear numpy scan; keyword search is term counting, not BM25 |
| API keys | Minted and hashed correctly, but no dependency resolves an `x-api-key` header to a user — the header waives CSRF and then still fails authentication |
| `ApiUsageLog` | Read by the usage endpoints, never written — they report zero |
| Alembic | Declared and wired into `make migrate`, but no `alembic.ini` and no versions directory; schema comes from `init_db()` |
| Search scoping | `kb_ids` and `score_threshold` are accepted and ignored; `search_type` does not change which indexes are consulted |
| Result shapes | `SearchResult` requires `chunk_id`/`document_id`/`title`/`score`; the index emits `doc_id`/`hybrid_score` — empty result sets validate, non-empty ones would not |

Read that table before estimating work on anything in the search or RAG path.

---

## 17. Repository layout

```
backend/          FastAPI app — routers, models, services, workers, telemetry
  app/api/        one module per domain, each with its own prefix and guard
  app/models/     SQLAlchemy models
  app/services/   indexing, retrieval, rag, llm, processing, embeddings, governance, platform
  app/workers/    Celery app, tasks, beat schedule
frontend/         Next.js app — marketing, dashboard, chat widget
dags/             Airflow DAGs: MinIO landing, dbt build, quality gate, catalog sync
dbt/              staging views and incremental marts
quality/          Great Expectations suite and checkpoint
config/           Airflow configuration
docker/           images, init SQL, nginx, Prometheus rules, Grafana dashboards, OpenMetadata workflows
tests/            pytest suite
workers/          standalone in-process worker (not wired to anything)
```

---

## 18. License

Apache License 2.0 — see [LICENSE](LICENSE).