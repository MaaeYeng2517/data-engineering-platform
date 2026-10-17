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

Apache Airflow, dbt, FastAPI, PostgreSQL, Redis, Elasticsearch, Qdrant, MinIO, OpenMetadata, Next.js, React, Tailwind CSS.

## Quick Start

```bash
docker compose up -d
cd frontend && npm install && npm run dev
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000

## Tests

```bash
cd frontend && npm run lint && npm run typecheck && npm test
```

## License

See LICENSE.
