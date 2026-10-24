# PYTHON_DATA_API_ARCHITECTURE.md

## 1. Overview
ออกแบบ Python Data API สำหรับ Enterprise Data Platform โดยใช้ FastAPI เป็นแกนกลาง รองรับ Batch และ Real-time ทำงานร่วมกับ PostgreSQL และ S3-Compatible Object Storage ภายใต้สถาปัตยกรรม Hybrid Cloud

## 2. Layered Architecture
| Layer | Purpose | Components |
| --- | --- | --- |
| **API Gateway** | TLS, Rate Limit, Routing, WAF | Traefik/NGINX |
| **Control Plane** | IAM/RBAC, Dataset Registry, Pipeline API, Job Management, Audit | FastAPI, Pydantic, Keycloak/OIDC |
| **Data Processing Plane** | Transform, Validate, Enrich | Celery Workers, Polars, PyArrow, Pandera |
| **Streaming Plane** | Event Ingestion/Consumption | Redpanda/Kafka-compatible, Consumer Groups |
| **Storage Plane** | Persistence & Objects | PostgreSQL, MinIO/S3, Parquet/Iceberg |
| **Observability Plane** | Metrics/Logs/Traces | OpenTelemetry, Prometheus, Grafana |

## 3. Hybrid Cloud Design
| Zone | Responsibility | Notes |
| --- | --- | --- |
| **On-Premises (Private Data Zone)** | เก็บและประมวลผลข้อมูลความละเอียดอ่อนสูง | Private PostgreSQL, MinIO, Local Workers, Private Connectors |
| **Cloud (App/Elastic)** | API, Orchestration, Scalable Workers | API Gateway, FastAPI, Celery Workers, Event Broker |
| **Private Connectivity** | เชื่อมต่อระหว่าง Zone | Site-to-Site VPN/Private Link, TLS, Allowlist, Firewall |

**กฎสำคัญ:** ข้อมูลที่มีความอ่อนไหวสูงไม่จำเป็นต้อง Replicate ขึ้น Cloud, ส่งเฉพาะ Metadata หรือข้อมูลที่ผ่านการลดความอ่อนไหว, Audit ทุกการส่งข้าม Zone

## 4. Technology Stack
| Component | Tech | Rationale |
| --- | --- | --- |
| Language | Python 3.12 | Ecosystem + Type hints |
| API | FastAPI + Pydantic v2 | Validation, OpenAPI, Async |
| ORM/Migration | SQLAlchemy 2.0 + Alembic | Migrations, Transactions |
| DB | PostgreSQL 16/18 | Metadata/Jobs/RBAC/Audit |
| Object Storage | MinIO/S3 | Raw/Curated/Artifacts |
| Data Engine | Polars + PyArrow | Fast columnar processing |
| Queue | Celery + RabbitMQ/Redis | Durable Jobs, Retry |
| Streaming | Redpanda/Kafka | Events, DLQ |
| AuthN/Z | Keycloak + OIDC (JWT) | SSO, RBAC |
| Validation | Pandera | Data Quality Rules |
| Observability | OTel, Prometheus, Grafana | Traces/Metrics/Logs |
| Testing | pytest, httpx, Testcontainers | Unit/Integration/Contract |
| Container | Docker/Kubernetes | Packaging/Orchestration |

## 5. API Design (v1)
Base: `/api/v1`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health/live` | Liveness |
| GET | `/health/ready` | Readiness (DB/Redis/Storage) |
| POST | `/datasets` | Create Dataset |
| GET | `/datasets` | List/Search Datasets |
| GET | `/datasets/{id}` | Get Dataset Detail |
| POST | `/datasets/{id}/upload-sessions` | Get Presigned/Signed Upload URL |
| POST | `/datasets/{id}/versions` | Register Dataset Version (checksum) |
| POST | `/ingestion/jobs` | Create Ingestion Job (202 Accepted) |
| GET | `/jobs/{id}` | Get Job Status |
| POST | `/pipelines` | Create Pipeline |
| POST | `/pipelines/{id}/runs` | Trigger Pipeline Run |
| POST | `/quality/checks` | Run Quality Check |
| GET | `/datasets/{id}/lineage` | Get Lineage |
| GET | `/audit-logs` | Query Audit Logs |
| POST | `/events` | Ingest Event (authorized) |

### Request/Response Patterns
- **202 Accepted** สำหรับ Async Jobs
- **Idempotency-Key** Header สำหรับ POST ที่อาจซ้ำ
- **Correlation/Trace ID** ทุก Request
- **Standard Error**: `{ "error": {"code": "...", "message": "...", "request_id": "...", "details": [...] } }`
- **Pagination**: `page`, `limit`, `total`

### Job State Machine
`QUEUED -> RUNNING -> (SUCCEEDED | FAILED | RETRY)`

ต้องมี `attempt_count`, `started_at`, `finished_at`, `error_code`, `trace_id`, `idempotency_key`

## 6. Security
- **AuthN:** OIDC JWT (Issuer/Audience/Exp/Signature)
- **AuthZ:** RBAC + Organization Scope + Resource-level checks (BOLA/IDOR prevention)
- **Transport:** TLS 1.3
- **Secrets:** Secret Manager/Vault, ไม่ Hardcode
- **Uploads:** Signed URL อายุสั้น, จำกัด Prefix/Bucket, Validate MIME/Signature
- **SSRF:** Deny Internal/Link-Local/Private IPs
- **SQL:** Parameterized Queries/ORM
- **Rate Limit:** Per IP/User/Client
- **Audit:** ทุก Action ที่มีผลต่อข้อมูล/สิทธิ์

## 7. Deployment Notes
- **Dev:** Docker Compose
- **Prod:** Kubernetes (หรือ Platform เดียวกันขององค์กร) + HPA, PDB, NetworkPolicy
- **Secrets:** External Secret Manager
- **Ingress:** TLS Termination + WAF
- **Private Network:** แยก Control/Data/Storage Plane
- **Observability:** OTel Collector -> Prometheus/Grafana/Loki/Tempo

## 8. Next Steps
1. Implement Core API (Health, Datasets, Jobs)
2. Add Job Queue (Celery)
3. Add Object Storage Upload Sessions
4. Add Quality/Lineage
5. Add Observability & Security Hardening
6. Load/Recovery Tests

**Version:** 1.0 | **Status:** Draft
