# DataAir

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
