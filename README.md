# DataAir

> 🌐 Live Demo: [https://maaelab-data-air.vercel.app/](https://maaelab-data-air.vercel.app/)

Enterprise Data Operating & Intelligence Platform — manages the complete data lifecycle from ingestion to AI agents.

## Features

- Unified ingestion from databases, warehouses and object stores
- Knowledge bases with versioning
- Hybrid search (semantic, vector, keyword)
- RAG with evaluation datasets
- Workflow orchestration with audit
- Data lineage
- Governance & audit with policy-as-code
- Analytics dashboards

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Recharts, React Flow
- **Database:** PostgreSQL 16 + pgvector
- **Search:** Hybrid (vector + keyword), Qdrant, Elasticsearch
- **Cache/Broker:** Redis, Celery + Flower
- **Storage:** MinIO (S3-compatible)
- **Orchestration:** Apache Airflow 2.x, dbt Core, Great Expectations
- **Catalog/Lineage:** OpenMetadata
- **AI/LLM:** OpenAI, Anthropic, Google Gemini, Ollama (multi-provider gateway with offline fallback)
- **Observability:** Prometheus, Grafana, OpenTelemetry (optional)
- **Content/Analytics:** React Markdown ecosystem, custom analytics API

## Quick Start

### Using Docker Compose (Recommended)
```bash
cp .env.example .env  # configure as needed
docker compose up -d
```

### Or run frontend/backend separately
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (docs at /docs)
- API Health: http://localhost:8000/health

## Tests

```bash
cd frontend && npm run lint && npm run typecheck && npm test
```

## License

See LICENSE.

## End-to-End System Flow

This diagram shows the complete journey from user interaction through document processing, indexing, search/RAG, and supporting data pipelines.

```mermaid
sequenceDiagram
    autonumber
    participant U as User (Browser)
    participant N as Nginx (:80)
    participant FE as Next.js (:3000)
    participant BE as FastAPI (:8000)
    participant DB as PostgreSQL
    participant R as Redis
    participant M as MinIO
    participant CW as Celery Worker
    participant IDX as Hybrid Index (In-Process)
    participant LLM as LLM Gateway
    participant AF as Airflow
    participant DBT as dbt
    participant GE as Great Expectations
    participant OM as OpenMetadata

    %% Authentication & UI
    U->>N: Access app
    N->>FE: Serve UI
    FE->>BE: Auth (JWT/CSRF) or public requests
    
    %% Document Upload & Ingestion
    U->>FE: Upload document
    FE->>BE: POST /documents/upload (multipart)
    BE->>DB: Create document record (status: processing)
    BE->>BE: Extract → Clean → Chunk (800/100 chars)
    BE->>DB: Store content/chunks/metadata
    alt Celery available
        BE-->>CW: Enqueue index_document_task(doc_id)
        CW->>BE: Fetch content
        CW->>CW: TokenChunker (300/50) → Embed
        CW->>IDX: Update vector/keyword indexes
        CW->>DB: Update document status (indexed)
    else Celery unavailable
        BE->>BE: _index_inline() → embed → index
        BE->>DB: Update status
    end

    %% Search
    U->>FE: Search query
    FE->>BE: POST /api/v1/search/
    BE->>IDX: Hybrid search (vec+kw, weights 0.6/0.4)
    BE->>BE: Rerank (overlap/pos/len)
    BE->>FE: Return ranked results with scores

    %% RAG
    U->>FE: Ask question (RAG)
    FE->>BE: POST /api/v1/rag/
    BE->>IDX: Retrieve top-k passages
    BE->>BE: ContextBuilder (dedupe→compress→budget 4000 tokens)
    BE->>LLM: Generate with numbered passages
    alt Provider succeeds
        LLM-->>BE: Answer + usage
    else All providers fail
        BE->>BE: Extractive fallback (quote passages)
    end
    BE->>FE: Answer + citations + sources

    %% Chat Streaming (Public)
    U->>FE: Chat publicly
    FE->>BE: POST /api/v1/chat/stream (SSE)
    BE->>BE: Ground context (≤6000 chars)
    BE->>LLM: Stream via provider chain
    LLM-->>BE: meta → deltas → done
    BE-->>FE: SSE frames

    %% Analytics & Blog
    FE->>BE: POST /track/page-view or /track/event (public)
    BE->>DB: Store Visitor/PageView/Event/Subscriber
    U->>FE: Browse /blog or /blog/[slug]
    FE->>BE: GET /api/v1/blog (public)

    %% Data Pipelines (Scheduled)
    AF->>M: Scan landing bucket (*/30)
    AF->>DBT: Build warehouse (02:00)
    AF->>GE: Data quality checks (03:30)
    AF->>OM: Catalog sync (04:00)
    DBT->>DB: Write staging/marts
    GE->>DB: Write quality audit
    OM->>DB: Update catalog/lineage
```

### Step-by-Step Explanation

1. **Access**: User hits site via Nginx; Next.js serves UI with auth via JWT/CSRF cookies.
2. **Upload**: Document uploaded → extracted/cleaned/chunked (char-level) → persisted to PostgreSQL.
3. **Indexing**: Celery worker (or inline fallback) tokenizes (300/50), embeds chunks, builds hybrid index (vector + keyword). Status tracked in DB.
4. **Search**: Hybrid retrieval merges scores (0.6 vector cosine + 0.4 keyword TF), reranks by overlap/position/length.
5. **RAG**: Top passages assembled with token budget, sent to LLM Gateway with citations instruction; degrades gracefully if no provider available.
6. **Chat**: Public SSE streaming with provider chain fallback; emits structured frames (meta/delta/done/error).
7. **Analytics/Blog**: Public endpoints track visitors/events/subscribers; blog serves published posts.
8. **Pipelines**: Airflow orchestrates MinIO ingestion → dbt transforms → GE validates → OM syncs catalog/lineage; all pipeline data lands in Postgres and is exposed via API/dashboard.

## Workflow Architecture (Component Workflow)

```mermaid
flowchart TB
    subgraph "Data Ingestion Workflow"
        W1[Source Files/Uploads] --> W2[Text Extraction & Cleaning]
        W2 --> W3[Char-level Chunking 800/100]
        W3 --> W4[Store in PostgreSQL]
        W4 --> W5[Enqueue to Celery/Inline Index]
        W5 --> W6[Token Chunking 300/50]
        W6 --> W7[Embedding Generation]
        W7 --> W8[Populate Hybrid Index]
    end
    
    subgraph "Retrieval Workflow"
        R1[User Query] --> R2[Hybrid Search - Vector+Keyword]
        R2 --> R3[Merge 0.6V + 0.4K]
        R3 --> R4[Reranker - Overlap/Pos/Len]
        R4 --> R5[Context Builder - Dedupe/Compress/Budget]
        R5 --> R6[Numbered Passages + Instructions]
    end
    
    subgraph "Generation Workflow"
        R6 --> G1[LLM Gateway - Provider Chain]
        G1 -->|Success| G2[Stream/Return Answer + Citations]
        G1 -->|All Fail| G3[Extractive Fallback]
        G3 --> G2
    end
    
    subgraph "Pipeline Workflow (Airflow)"
        P1[MinIO Landing] -->|*/30 min| P2[dbt Build - Staging/Marts]
        P2 -->|02:00| P3[Great Expectations QA]
        P3 -->|03:30| P4[OpenMetadata Catalog Sync]
        P4 -->|04:00| P5[Audit & Lineage Updated]
    end
    
    W8 --> R2
```

## 21. Tool Connectivity & Data Flow Diagram

### Complete System Integration Map

```mermaid
flowchart LR
    subgraph "External"
        EXT[External Files/URLs]
        LLM_API[LLM Providers<br/>OpenAI/Anthropic/Google/Ollama]
    end
    
    subgraph "Frontend"
        UI[Next.js App Router]
        CHAT_W[Chat Widget + SSE]
        BLOG_UI[Blog Pages + Admin]
        DASH[Dashboard/Analytics]
    end
    
    subgraph "API Gateway"
        API[FastAPI Backend]
        MW[Middleware<br/>CORS/CSRF/JWT/RateLimit]
        AUTH[Auth<br/>Sessions/API Keys]
    end
    
    subgraph "Core Services"
        DOC[Document Service]
        SRCH[Search/Retrieval Engine]
        RAG_S[RAG Engine]
        CHAT_S[Chat Gateway]
        BLOG_S[Blog Service]
        ANA_S[Analytics Service]
        GOV[Governance/Profiles]
    end
    
    subgraph "Data Stores"
        PG[(PostgreSQL<br/>+pgvector)]
        RD[(Redis)]
        MIN[(MinIO S3)]
        QD[(Qdrant)]
        ES[(Elasticsearch)]
    end
    
    subgraph "Processing"
        CEL[Celery Workers<br/>queues: default/indexing/ingestion]
        FLW[Flower]
    end
    
    subgraph "Data Platform"
        AF[Airflow<br/>Scheduler/Web/Triggerer]
        DBT[dbt Core]
        GE[Great Expectations]
        OM[OpenMetadata]
    end
    
    subgraph "Observability"
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    %% Connections
    EXT --> UI
    UI <-->|HTTP/REST + SSE| NGINX[Nginx:80] --> API
    NGINX --> UI
    
    API --> MW --> AUTH
    AUTH --> DOC & SRCH & RAG_S & CHAT_S & BLOG_S & ANA_S & GOV
    
    DOC -->|store chunks/content| PG
    DOC -->|enqueue| CEL
    CEL -->|index/embed| SRCH
    
    SRCH -->|vector search| PG & QD
    SRCH -->|keyword| ES
    SRCH -->|cache| RD
    SRCH -->|hybrid merge+rerank| RAG_S
    
    RAG_S -->|context build| CHAT_S
    CHAT_S -->|provider chain| LLM_API
    ANA_S -->|events/views/subs| PG
    BLOG_S -->|posts/tags| PG
    
    CEL <-->|broker/results| RD
    FLW --> CEL
    DOC -->|objects| MIN
    
    MIN --> AF
    AF --> DBT & GE & OM
    DBT --> PG
    GE --> PG
    OM --> PG
    
    API & CEL & AF --> PROM
    PROM --> GRAF
```

### Data Flow Description

1. **User Input → API**: Browser requests flow through Nginx to FastAPI with CORS/CSRF/JWT/API-key middleware enforcing auth and rate limits.
2. **Application Services → Storage**: Documents stored in PostgreSQL; objects in MinIO; embeddings/indexes in PG (pgvector), Qdrant, Elasticsearch; state/cache in Redis.
3. **Async Processing**: Heavy work (chunking/embedding/reindexing) enqueued to Celery workers (indexing/ingestion queues); Flower monitors.
4. **AI Path**: Search merges vector+keyword (hybrid) with reranking → ContextBuilder builds bounded context → LLM Gateway tries provider chain with offline fallback → SSE streams back.
5. **Platform Pipelines**: Airflow ingests from MinIO, triggers dbt transforms, runs GE quality checks, syncs metadata to OpenMetadata; all results persisted to Postgres for API consumption.
6. **Analytics/Content**: Public blog and analytics write/read tenant-scoped data; frontend dashboards visualize via API.
7. **Observability**: Prometheus scrapes metrics from API/workers/Airflow; Grafana visualizes.

### Integration Points Summary

| Integration | Direction | Protocol | Purpose |
|---|---|---|---|
| Browser ↔ Nginx/Frontend/API | Bidirectional | HTTP/HTTPS, SSE | UI, auth, chat streaming |
| API ↔ PostgreSQL | Read/Write | SQL (asyncpg) | Core data, vectors (pgvector), blog, analytics |
| API/Workers ↔ Redis | Read/Write | RESP | Broker, cache, rate limiting |
| API/Workers ↔ MinIO | Read/Write | S3 API | Object/file storage |
| Workers ↔ Qdrant/ES | Read/Write | HTTP | Vector/keyword indexes (secondary) |
| API ↔ LLM Providers | Request/Response (stream) | HTTP | Chat/RAG generation |
| Airflow ↔ MinIO/DB/OM/GE/dbt | Orchestrated | Various | ETL, QA, catalog, transforms |
| All → Prometheus/Grafana | Metrics | HTTP scrape | Observability |

## 22. Payment-Gated Signup (Subscribe Before Use)

A paid plan does not create an account. The workspace is opened only after the
payment is confirmed, so nobody can use the platform on a plan they have not
paid for.

```mermaid
sequenceDiagram
    autonumber
    participant U as Visitor
    participant FE as /subscribe
    participant BE as POST /billing/subscribe
    participant DB as PostgreSQL
    participant ST as Stripe
    participant WH as /billing/webhook
    participant SS as /subscribe/success

    U->>FE: Pick a plan, enter email + password
    FE->>BE: POST /billing/subscribe {email, password, plan_code}
    BE->>DB: INSERT pending_registrations (status=pending)
    alt Free plan (price_cents = 0)
        BE->>DB: CREATE tenant + user + plan + subscription
        BE-->>FE: status=activated + access_token
        FE->>U: Redirect to /dashboard
    else Paid plan
        BE->>ST: checkout.Session.create (mode=subscription)
        ST-->>BE: session_id + checkout_url
        BE->>DB: status=checkout_created
        BE-->>FE: checkout_url
        FE->>U: Redirect to Stripe Checkout
        U->>ST: Pay
        ST->>WH: checkout.session.completed
        WH->>DB: CREATE tenant + user + plan + subscription
        WH->>DB: status=completed
        U->>SS: Return with ?session_id=…
        SS->>BE: GET /billing/subscribe/status (poll every 2s)
        BE->>ST: checkout.Session.retrieve (fallback if webhook is late)
        BE-->>SS: activated=true
        SS->>U: "เข้าสู่ workspace"
    end
```

### The rules it enforces

- **No account before payment.** A paid signup writes only a
  `pending_registrations` row. The user, tenant and subscription appear when
  Stripe confirms the payment.
- **The free plan skips the wait.** It activates in the same request and
  returns the session cookies, so there is no dead time for free users.
- **The webhook is the primary path; the status poll is the fallback.** A
  delayed or missed webhook still unblocks the user, because the poll asks
  Stripe directly.
- **Delivery is idempotent.** Stripe can deliver the same webhook twice. The
  second delivery finds the account already there and closes the
  registration instead of creating a second user.
- **The password is stored hashed on the pending row,** so the browser never
  has to resend it after the payment.

### Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/v1/billing/public-plans` | public | Plan catalogue for the pricing page |
| `POST /api/v1/billing/subscribe` | public | Start a signup; returns a checkout URL or activates a free plan |
| `GET /api/v1/billing/subscribe/status` | public | Poll until the paid signup is activated |
| `POST /api/v1/billing/checkout` | user | Checkout for an already-registered user upgrading |
| `POST /api/v1/billing/portal` | user | Stripe customer portal |
| `POST /api/v1/billing/webhook` | Stripe signature | Stripe events, including the activation |

### Where the code lives

| Piece | Location |
|---|---|
| `PendingRegistration` model | `backend/app/models/billing.py` |
| Account activation (tenant + user + plan + subscription) | `backend/app/services/onboarding.py` |
| Subscribe, status and webhook handling | `backend/app/api/billing.py` |
| Schemas | `backend/app/schemas/__init__.py` (`SubscribeRequest`, `SubscribeResponse`, `SubscribeStatusResponse`, `PublicPlanResponse`) |
| Pricing page | `frontend/app/subscribe/page.tsx` |
| Payment status page | `frontend/app/subscribe/success/page.tsx` |
| API client | `frontend/lib/api/billing.ts` |

### Configuration

`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_SUCCESS_URL` and
`STRIPE_CANCEL_URL` drive the flow. `SAAS_PLANS` overrides the plan
catalogue, and every paid plan needs a `stripe_price_id` — the production
config check refuses to start without one.
