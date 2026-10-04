# DataOS Architecture Document

## Overview

DataOS is an Enterprise Data Operating Platform built as a **Modular Monolith** with clear service boundaries, allowing future extraction into microservices.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Dashboard│ │Data Studio│ │Explorer  │ │Knowledge │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Auth    │ │ Data     │ │Workflow  │ │  AI/ML   │           │
│  │  IAM     │ │ Ingestion│ │ Engine   │ │ Gateway  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  PostgreSQL   │   │    Redis      │   │    MinIO      │
│  (Primary DB) │   │  (Cache/Queue)│   │ (Object Store)│
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA PROCESSING LAYER                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Ingestion│ │Processing│ │ Quality  │ │ Workflow │           │
│  │ Workers  │ │ Workers  │ │ Workers  │ │ Workers  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Vector Store │   │  Search Eng.  │   │  AI Models    │
│  (pgvector/   │   │ (Elasticsearch│   │ (OpenAI,      │
│   Qdrant)     │   │  / BM25)      │   │  Anthropic,   │
│               │   │               │   │  Ollama)      │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Module Boundaries

### Core Modules (Internal Packages)

```
backend/
├── app/
│   ├── api/           # API route handlers (thin layer)
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas (request/response)
│   ├── services/      # Business logic (domain services)
│   ├── dependencies/  # FastAPI dependencies
│   └── security/      # Auth, CSRF, encryption
├── config.py          # Configuration management
├── database.py        # DB session management
└── main.py            # Application entry point
```

### Service Modules (Extractable)

| Module | Responsibility | Future Extraction |
|--------|----------------|-------------------|
| `ingestion` | Data source connectors, extraction | Ingestion Service |
| `processing` | Transform, clean, validate | Processing Service |
| `quality` | Data quality rules, scoring | Quality Service |
| `workflow` | Workflow engine, scheduler | Workflow Service |
| `metadata` | Catalog, lineage, governance | Metadata Service |
| `knowledge` | Document processing, RAG | Knowledge Service |
| `ai` | Model gateway, agents, tools | AI Service |

## Data Flow

### Ingestion Pipeline
```
Source → Connector → Raw Storage → Validation → Cleaning → Transform → Lakehouse
```

### Processing Pipeline
```
Bronze (Raw) → Silver (Cleaned/Validated) → Gold (Business-Ready)
```

### RAG Pipeline
```
Question → Query Processing → Retrieval → Reranking → Context → LLM → Answer
```

### LLM Gateway

Every generative call — homepage chat, RAG answers, evaluation runs — goes
through one gateway so a deployment can mix vendors behind a single API.

```
Chat / RAG request
      │
      ▼
┌─────────────────────────────┐
│  LLMGateway (resolve+retry) │
└─────────────┬───────────────┘
              │  first configured provider wins, then the next, then offline
   ┌──────────┼───────────┬────────────┬───────────┐
   ▼          ▼           ▼            ▼           ▼
 OpenAI   Anthropic   Google Gemini   Ollama    Offline
(chat    (messages)  (generateContent) (local)  (deterministic
completions)                              /api/chat)  responder)
```

- **Providers**: `openai`, `anthropic`, `google`, `ollama`, `offline`.
- **Selection**: `LLM_PROVIDER` pins one; otherwise the first *available*
  provider wins. Availability for Ollama is a cached reachability probe, so a
  local runtime that is not running never appears in the model picker.
- **Model discovery**: providers are queried for their live model list and
  cached (`LLM_MODEL_CACHE_TTL`); a pinned default that is not installed is
  substituted rather than failing the request.
- **Degradation**: automatic selection always ends in the offline responder, so
  a broken or rate-limited provider yields a labelled answer instead of a 502.
  An explicitly requested provider is never silently swapped.
- **Transport**: `generate` returns one completion, `stream` yields fragments,
  and `stream_events` adds `meta`/`delta`/`done` events for SSE consumers.

## Technology Stack

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Query (TanStack Query)
- **Visualization**: React Flow, Recharts
- **Build**: Turbopack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: JWT + bcrypt + CSRF

### Data
- **Primary**: PostgreSQL 16+
- **Cache/Queue**: Redis 7+
- **Object Storage**: MinIO (S3-compatible)
- **Vector**: pgvector (primary), Qdrant (fallback)
- **Search**: Elasticsearch + BM25
- **Processing**: Pandas, Polars, DuckDB

### Workflow
- **Abstraction**: Custom workflow engine
- **Future**: Celery, Temporal, Airflow compatible

### Monitoring
- **Telemetry**: OpenTelemetry
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logging**: Structured JSON logs

### Infrastructure
- **Container**: Docker + Docker Compose
- **Orchestration**: Kubernetes-ready
- **CI/CD**: GitHub Actions

## Database Schema Overview

### Core Tables
- `tenants` - Multi-tenant isolation
- `users` - User accounts with RBAC
- `roles` / `permissions` - Fine-grained access control
- `membership_plans` / `subscriptions` - SaaS billing

### Data Tables
- `data_sources` - Connector configurations
- `ingestion_jobs` - Ingestion execution tracking
- `raw_files` - Immutable raw storage references
- `datasets` - Logical datasets with versions
- `dataset_columns` - Schema metadata
- `processing_jobs` - Transformation execution

### Quality Tables
- `quality_rules` - Validation rules
- `quality_results` - Execution results
- `quality_scores` - Aggregated scores

### Metadata Tables
- `metadata_catalog` - Global search index
- `lineage_nodes` / `lineage_edges` - Data lineage graph
- `governance_policies` - Classification & policies

### Workflow Tables
- `workflows` - Workflow definitions (React Flow JSON)
- `workflow_runs` - Execution instances
- `workflow_tasks` - Individual task executions

### Knowledge Tables
- `knowledge_bases` - KB containers
- `documents` - Uploaded documents
- `chunks` - Text chunks with embeddings
- `entities` / `relationships` - Knowledge graph

### Observability Tables
- `audit_logs` - Centralized audit trail
- `api_usage_logs` - API consumption tracking

## Security Model

### Authentication
- JWT access tokens (15 min default)
- JWT refresh tokens (30 days)
- HttpOnly Secure cookies
- CSRF protection (double-submit cookie)

### Authorization
- Role-based (Guest, Member, Admin, Superuser)
- Permission-based (resource:action)
- Tenant isolation (mandatory tenant_id filter)
- API key scopes

### Data Protection
- Encryption at rest (PostgreSQL TDE, MinIO SSE)
- Encryption in transit (TLS 1.3)
- Secrets management (env vars, Docker secrets)
- PII detection & masking

## Scalability Considerations

### Horizontal Scaling
- Stateless API workers (FastAPI + Uvicorn workers)
- Redis for distributed caching & queue
- PostgreSQL read replicas
- MinIO distributed mode

### Performance
- Connection pooling (SQLAlchemy asyncpg)
- Async I/O throughout
- Batch processing for ingestion
- Vector search optimization (HNSW indexes)

### Reliability
- Health checks (/health, /ready)
- Graceful shutdown
- Retry with exponential backoff
- Circuit breakers for external APIs

## Deployment Architecture

### Development
```
docker-compose.yml
├── postgres
├── redis
├── minio
├── elasticsearch
├── qdrant
├── backend (FastAPI)
├── frontend (Next.js dev)
└── worker (background tasks)
```

### Production (Kubernetes)
```
Namespace: dataos
├── Deployment: api (3+ replicas, HPA)
├── Deployment: worker (2+ replicas)
├── Deployment: frontend (2+ replicas)
├── StatefulSet: postgres (primary + replica)
├── StatefulSet: redis (cluster)
├── StatefulSet: minio (distributed)
├── StatefulSet: elasticsearch
├── StatefulSet: qdrant
├── Ingress: nginx (TLS termination)
├── ConfigMap: app config
├── Secret: DB passwords, API keys
└── ServiceMonitor: Prometheus
```

## API Design

### Versioning
- URL versioning: `/api/v1/`
- Backward compatible changes only
- Deprecation headers for removed endpoints

### Standards
- RESTful conventions
- JSON request/response
- Standardized error format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [...]
  }
}
```

### Pagination
- Cursor-based for large datasets
- Offset/limit for small datasets
- Max page size: 100

### Filtering/Sorting
- Query parameters: `?filter[field]=value&sort=-created_at`
- Standardized across all list endpoints

### Chat Endpoints

Public, rate limited, and exempt from CSRF because they are stateless and never
act on a cookie-authenticated session.

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/v1/chat/providers` | GET | Providers and models this deployment can serve |
| `/api/v1/chat` | POST | One complete answer as JSON |
| `/api/v1/chat/stream` | POST | The same answer as server-sent events |

`POST /api/v1/chat/stream` emits three event types:

```
event: meta   data: {"provider": "ollama", "model": "qwen3:8b", "degraded": false}
event: delta  data: {"text": "Data"}
event: delta  data: {"text": "Air"}
event: done   data: {"latency_ms": 812.4, "token_usage": {...}, "sources": [...]}
event: error  data: {"detail": "..."}   # only when nothing was streamed yet
```

A caller may pass `kb_ids` to ground the answer in retrieved passages; the
retrieved snippets are returned in `sources`. Clients cannot send a system
prompt: the server owns it, so a public endpoint cannot be talked out of its
guardrails.

## Extension Points

### Connector Plugin
```python
class DataConnector(ABC):
    async def connect() -> bool
    async def test_connection() -> Dict
    async def discover_schema() -> Dict
    async def extract() -> AsyncIterator[Record]
    async def health_check() -> Dict
```

### Processor Plugin
```python
class DataProcessor(ABC):
    async def validate(data: DataFrame) -> ValidationResult
    async def clean(data: DataFrame) -> DataFrame
    async def transform(data: DataFrame, config: Dict) -> DataFrame
```

### Quality Rule Plugin
```python
class QualityRule(ABC):
    async def evaluate(dataset: Dataset) -> QualityResult
```

### AI Tool Plugin
```python
class Tool(ABC):
    name: str
    description: str
    parameters: JSONSchema
    async def execute(params: Dict) -> Any
```

## Future Extraction Strategy

When a module reaches sufficient maturity and independent scaling needs:

1. **Create separate repository**
2. **Define gRPC/REST contract**
3. **Extract shared models to common package**
4. **Deploy as independent service**
5. **Update API gateway routing**
6. **Implement distributed tracing**
7. **Add service mesh (Istio/Linkerd)**

## Decision Records

See `docs/adr/` for Architecture Decision Records.