# ENTERPRISE_DATA_API_README.md

## Enterprise Python Data API

Production-oriented Data API สำหรับองค์กร ใช้ FastAPI + PostgreSQL + S3-Compatible Object Storage + Celery + Polars

## Features
- **Control Plane:** Dataset Registry, Job Orchestration, RBAC/Audit
- **Processing Plane:** Batch via Polars/PyArrow, validated with Pandera
- **Streaming Ready:** Redpanda/Kafka compatible consumers
- **Hybrid Cloud Ready:** แยก On-Prem/Cloud Zones + Private Connectivity
- **Security First:** OIDC/JWT, RBAC, Signed URLs, Audit Logs
- **Observable:** OpenTelemetry, Prometheus, Grafana

## Quick Start (Dev)
```bash
# Copy env
cp .env.example .env

# Start services
docker compose -f infra/docker/compose.dev.yaml up --build

# API Docs
# http://localhost:8000/docs
# http://localhost:8000/redoc
```

## API Base
`/api/v1`

## Key Endpoints
| Method | Path | Description |
| --- | --- | --- |
| GET | `/health/live` | Liveness |
| GET | `/health/ready` | Readiness |
| POST | `/ingestion/jobs` | Create batch job (202) |
| GET | `/jobs/{id}` | Job status |
| POST | `/datasets/{id}/upload-sessions` | Get signed upload URL |

## Environment Variables (example)
```env
APP_ENV=dev
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/enterprise_data
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_RAW=enterprise-raw
OIDC_ISSUER=https://keycloak.local/realms/enterprise
OIDC_AUDIENCE=enterprise-data-api
```

## Testing
```bash
pytest -v
pytest tests/integration -v
```

## Security Notes
- ห้ามเปิด DB/Redis/Storage สู่ Public
- ใช้ Signed URL อายุสั้น
- บันทึก Audit ทุก Action ที่มีผลต่อข้อมูล
- ใช้ Least Privilege สำหรับ Service Account

## License
Internal Use
