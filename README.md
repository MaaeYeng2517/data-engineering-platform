# DataAir — Knowledge Engineering Platform

> Live demo: [https://maaelab-data-air.vercel.app/](https://maaelab-data-air.vercel.app/)

## 19. System Tools & Integrations

The platform includes built-in tools and integrations to support the knowledge engineering lifecycle:

| Tool/Service | Purpose | Status | Endpoint/Notes |
|---|---|---|---|
| FastAPI Backend | Core API, auth, RAG, search | Active | http://localhost:8000/docs |
| Next.js Frontend | Web UI, blog, chat, dashboard | Active | http://localhost:3000 |
| PostgreSQL + pgvector | App data + vector storage | Active | Configured via DATABASE_URL |
| Redis | Celery broker/cache | Active | Used by workers & chat rate limiting |
| Qdrant | Vector DB (alternative/target) | Configured | Health-probed; indexing path uses in-process index |
| Elasticsearch | Keyword search | Configured | Health-probed; hybrid search uses in-process keyword index |
| MinIO | Object storage for files | Active | S3-compatible, used by pipelines |
| Airflow | ETL/orchestration DAGs | Active | http://localhost:8080 |
| dbt | Data transformations | Active | Runs in unified image/pipelines |
| Great Expectations | Data quality checks | Active | Quality gate in DAGs |
| OpenMetadata | Data catalog & lineage | Active | http://localhost:8585 |
| Celery + Flower | Async task processing | Configurable | Worker queues (default/indexing/ingestion); degrades if not installed |
| Prometheus + Grafana | Observability/metrics | Active | http://localhost:9090, http://localhost:3001 |
| LLM Gateway | Multi-provider chat/RAG | Active | Supports OpenAI/Anthropic/Google/Ollama + offline fallback |
| Blog Module | Content management | Active | Public blog + admin CRUD at /blog |
| Analytics Module | Visitor/event tracking | Active | Public tracking endpoints + dashboard |
| Auth (JWT/CSRF/API keys) | Security | Active | Session cookies + API key auth (dk_* prefixed) |

