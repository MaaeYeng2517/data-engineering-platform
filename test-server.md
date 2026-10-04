# Server Test Report

ทดสอบจริงทุก service ใน `data-engineering-platform`
อัปเดตล่าสุด **2026-10-04 07:09 (+07)** · Docker Desktop · 26 containers (23 running + 3 init exit 0)

| สรุป | จำนวน |
|---|---|
| สำเร็จ | 26 |
| ไม่สำเร็จ | 0 |
| พบปัญหาแล้วแก้ครบ | 6 (ข้อ 4 ไม่ต้องแก้) |

หน้าเว็บติดตามสถานะสด: **http://localhost:3000/system** (ไม่ต้อง login)

---

## ผลการทดสอบ

| Service Name | Tools | Port | Status |
|---|---|---|---|
| `postgres` | psql 16 · pgvector | 5432 | สำเร็จ |
| `redis` | redis-cli 7.2 | 6379 | สำเร็จ |
| `minio` | mc · S3 API | 9000 / 9001 | สำเร็จ |
| `elasticsearch` | REST API 8.17 | 9200 | สำเร็จ |
| `qdrant` | REST + gRPC 1.12 | 6333 / 6334 | สำเร็จ |
| `backend` | FastAPI + uvicorn | 8000 | สำเร็จ |
| `frontend` | Next.js 14 · Node 20 | 3000 | สำเร็จ |
| `nginx` | nginx:alpine | 80 / 443 | สำเร็จ |
| `airflow-webserver` | Apache Airflow 2.10.3 | 8080 | สำเร็จ |
| `airflow-scheduler` | Airflow scheduler | internal 8080 | สำเร็จ |
| `airflow-triggerer` | Airflow triggerer | internal 8080 | สำเร็จ |
| `airflow-init` | `airflow db migrate` | — | สำเร็จ |
| `worker` | Celery 5.4 worker | internal | สำเร็จ |
| `scheduler` | Celery beat | internal | สำเร็จ |
| `flower` | Flower 2.0 | 5555 | สำเร็จ |
| `openmetadata` | OpenMetadata 1.5.11 | 8585 | สำเร็จ |
| `openmetadata-init` | `openmetadata-ops.sh migrate` | — | สำเร็จ |
| `openmetadata-ingestion` | Airflow 2.9.1 scheduler | internal 8080 | สำเร็จ |
| `openmetadata-ingestion-init` | `airflow db migrate` (airflow_om) | — | สำเร็จ |
| `prometheus` | Prometheus | 9090 | ยังไม่ผ่าน |
| `grafana` | Grafana 13.2.3 | 3001 | สำเร็จ |
| `postgres-exporter` | prometheuscommunity 0.16 | internal 9187 | สำเร็จ |
| `redis-exporter` | oliver006 v1.66 | internal 9121 | สำเร็จ |
| `python` | JupyterLab 4.3.3 · Python 3.11.16 | 8888 | สำเร็จ |
| `dbt` | dbt-core 1.9.1 | — | สำเร็จ |
| `great-expectations` | GX 0.18.15 | — | สำเร็จ |

---

## Data Layer

| Service | คำสั่งที่ทดสอบ | ผลลัพธ์ | Status |
|---|---|---|---|
| `postgres` | `psql -c "SELECT count(*) FROM information_schema.tables"` | `connect ok, tables=20` | สำเร็จ |
| `postgres` | `SELECT datname FROM pg_database` | `dataair, airflow, openmetadata_db, airflow_om` | สำเร็จ |
| `redis` | `redis-cli ping` | `PONG` | สำเร็จ |
| `redis` | `redis-cli DBSIZE` | `56` | สำเร็จ |
| `minio` | `GET /minio/health/live` | `200` | สำเร็จ |
| `elasticsearch` | `GET /_cluster/health` | `yellow · 57/57 primary shards · 1 node` | สำเร็จ |
| `qdrant` | `GET /collections` | `{"collections":[]},"status":"ok","time":0.006` | สำเร็จ |

## Application

| Service | คำสั่งที่ทดสอบ | ผลลัพธ์ | Status |
|---|---|---|---|
| `backend` | `GET /health` | `200` | สำเร็จ |
| `backend` | `POST /api/v1/auth/register` | `access_token + user` | สำเร็จ |
| `backend` | `GET /api/v1/auth/me` | `verify.run@example.com member` | สำเร็จ |
| `backend` | `GET /api/v1/auth/csrf-token` | `token returned` | สำเร็จ |
| `backend` | `POST /api/v1/knowledge-bases/` | `736138a5-…` | สำเร็จ |
| `backend` | `POST /api/v1/documents/` | `d20325ae-…` | สำเร็จ |
| `backend` | `POST /api/v1/search/` | `{"results":[],"total":0,"latency_ms":0.77}` | สำเร็จ |
| `backend` | `GET /openapi.json` | `114 endpoints` | สำเร็จ |
| `backend` | `GET /metrics` | `200` (Prometheus exposition) | สำเร็จ |
| `frontend` | `GET /` | `200` | สำเร็จ |
| `frontend` | `GET /documents` | `200` | สำเร็จ |
| `frontend` | `GET /login` | `200` | สำเร็จ |
| `frontend` | `GET /register` | `200` | สำเร็จ |
| `frontend` | `GET /dashboard` | `200` | สำเร็จ |
| `frontend` | `GET /dashboard/tools` | `200` | สำเร็จ |
| `frontend` | `GET /dashboard/stacks` | `200` | สำเร็จ |
| `frontend` | `GET /dashboard/documents` | `200` | สำเร็จ |
| `frontend` | `GET /dashboard/search` | `200` | สำเร็จ |
| `frontend` | `GET /api/health` | `200` | สำเร็จ |
| `nginx` | `GET http://localhost/` | `200` (proxy → frontend) | สำเร็จ |
| `nginx` | `GET https://localhost/documents` | `200` (TLS) | สำเร็จ |
| `nginx` | `GET http://localhost/metrics` | `200` (proxy → backend) | สำเร็จ |
| `nginx` | `GET http://localhost/health` | `200` (proxy → backend) | สำเร็จ |

## Orchestration

| Service | คำสั่งที่ทดสอบ | ผลลัพธ์ | Status |
|---|---|---|---|
| `airflow-webserver` | `GET /health` | `metadatabase=healthy, heartbeat 23:36:01` | สำเร็จ |
| `airflow-webserver` | `airflow dags list` | `4 DAGs loaded` | สำเร็จ |
| `airflow-scheduler` | heartbeat ใน `/health` | `ต่อเนื่อง` | สำเร็จ |
| `airflow-triggerer` | log | `0 triggers currently running` ทุกนาที | สำเร็จ |
| `airflow-init` | exit code | `Exited (0)` หลัง `db migrate` | สำเร็จ |
| `worker` | `celery_app.control.ping(timeout=5)` | `workers replied: 1` | สำเร็จ |
| `worker` | `control.inspect().active_queues()` | `default, indexing, ingestion, celery` | สำเร็จ |
| `scheduler` | Celery beat | `ทำงานอยู่` | สำเร็จ |
| `flower` | `GET /` | `200` (UI) | สำเร็จ |
| `flower` | `GET /api/workers` | `200` (เปิด REST API แล้ว) | สำเร็จ |

### DAG ที่โหลดได้

| DAG | File | Owners | Paused | Status |
|---|---|---|---|---|
| `catalog_sync` | `catalog_sync.py` | data-platform | False | สำเร็จ |
| `data_quality_check` | `data_quality_check.py` | data-platform | False | สำเร็จ |
| `ingest_minio_landing` | `ingest_minio_landing.py` | data-platform | False | สำเร็จ |
| `warehouse_build` | `warehouse_build.py` | data-platform | False | สำเร็จ |

## Catalog & Observability

| Service | คำสั่งที่ทดสอบ | ผลลัพธ์ | Status |
|---|---|---|---|
| `openmetadata` | `GET /api/v1/system/version` | `1.5.11 (67c3ed75)` | สำเร็จ |
| `openmetadata` | `information_schema.tables` | `86 tables` | สำเร็จ |
| `openmetadata-init` | exit code | `Exited (0)` | สำเร็จ |
| `openmetadata-ingestion` | log | `DagFileProcessorManager` ทำงาน 15 รอบ | สำเร็จ |
| `openmetadata-ingestion-init` | exit code | `Exited (0)` | สำเร็จ |
| `grafana` | `GET /api/health` | `database=ok, version=13.2.3` | สำเร็จ |
| `grafana` | `GET /api/datasources` | `200 · 3 datasources` | สำเร็จ |
| `prometheus` | `GET /api/v1/targets` | `7 targets · 7 up` | สำเร็จ |
| `prometheus` | scrape `backend`, `celery-worker`, `scheduler` | `up` ทั้งสาม job | สำเร็จ |
| `postgres-exporter` | scrape จาก Prometheus | `up` | สำเร็จ |
| `redis-exporter` | scrape จาก Prometheus | `up` | สำเร็จ |

### Prometheus scrape targets

| Job | Health | Error | Status |
|---|---|---|---|
| `flower` | up | — | สำเร็จ |
| `prometheus` | up | — | สำเร็จ |
| `postgres-exporter` | up | — | สำเร็จ |
| `redis-exporter` | up | — | สำเร็จ |
| `backend` | up | — | สำเร็จ |
| `celery-worker` | up | — | สำเร็จ |
| `scheduler` | up | — | สำเร็จ |

## Toolbox

| Service | คำสั่งที่ทดสอบ | ผลลัพธ์ | Status |
|---|---|---|---|
| `worker` | `GET :9100/metrics` | `200` (Prometheus scrape ได้) | สำเร็จ |
| `scheduler` | `GET :9100/metrics` | `200` (Prometheus scrape ได้) | สำเร็จ |
| `python` | `jupyter lab --version` | `4.3.3` | สำเร็จ |
| `python` | `python --version` | `Python 3.11.16` | สำเร็จ |
| `python` | `GET /api` | `200` | สำเร็จ |
| `dbt` | `dbt --version` | `Core 1.9.1` | สำเร็จ |
| `great-expectations` | `great_expectations --version` | `0.18.15` | สำเร็จ |

---

## หมายเหตุ / ข้อควรแก้

| # | ปัญหา | สาเหตุ | แนวทางแก้ | สถานะ |
|---|---|---|---|---|
| 1 | Prometheus scrape `backend` ล้ม | โค้ดไม่มี route `/metrics` | เพิ่ม route `/metrics` ที่คืน `generate_latest()` ใน `backend/main.py:110` | **แก้แล้ว** — `backend /metrics` → 200 |
| 2 | Prometheus scrape `celery-worker` / `scheduler` ล้ม | ไม่ได้เปิด HTTP server ที่พอร์ต 9100 | `start_http_server(9100)` ใน `celery_worker.py:19` และเพิ่ม `celery_beat.py` เป็น entrypoint ของ scheduler | **แก้แล้ว** — ทั้งคู่ → 200, scrape `up` |
| 3 | Grafana `/api/datasources` ตอบ 401 | volume `grafana_data` เก็บรหัสผ่านจากรอบแรก | ลบ volume แล้วสร้างใหม่ ทำให้รหัสผ่านตรงกับ `${GRAFANA_PASSWORD}` | **แก้แล้ว** — 200, ได้ 3 datasources |
| 4 | Elasticsearch สถานะ `yellow` | single-node ไม่มี replica ให้จัดสรร | ไม่ต้องแก้ | ไม่ต้องแก้ |
| 5 | Flower REST API ปิด | ไม่ได้ตั้ง `FLOWER_UNAUTHENTICATED_API` | เพิ่ม env ใน `docker-compose.yml` | **แก้แล้ว** — `/api/workers` → 200 |
| 6 | nginx ตอบ 502 หลัง backend restart | nginx cache IP ของ upstream ตอน startup (`upstream` block ไม่มี `resolver`) | เปลี่ยน `proxy_pass` เป็นแบบตัวแปร + `resolver 127.0.0.11 valid=10s` ใน `docker/nginx.conf` | **แก้แล้ว** — recreate backend แล้วยัง 200 โดยไม่ต้อง restart nginx |
| 7 | หน้า monitoring รายงาน nginx เป็น "degraded" แต่ไม่บอกสาเหตุ | `_timed_http` ใช้ `detail` ทั้งกรณีสำเร็จและล้มเหลว | รวม HTTP status เข้าไปใน detail | **แก้แล้ว** |

### ผลหลังแก้

| ตรวจสอบ | ผลลัพธ์ |
|---|---|
| Prometheus scrape targets | `7/7 up` |
| สรุประบบทั้งหมด | `18 services · healthy 18 · degraded 0 · down 0 · 100%` |
| หน้าเว็บ `/system` | `200` |
| Restart count ของ container ที่แก้ | `0` ทั้งหมด (ไม่มี restart loop) |

---

## Port ที่ publish ออก host

| Port | Service | จุดเข้าใช้งาน |
|---|---|---|
| 80 / 443 | `nginx` | http://localhost · https://localhost |
| 3000 | `frontend` | http://localhost:3000 |
| 3001 | `grafana` | http://localhost:3001 |
| 5432 | `postgres` | postgresql://dataair:dataair@localhost:5432 |
| 5555 | `flower` | http://localhost:5555 |
| 6333 / 6334 | `qdrant` | http://localhost:6333 |
| 6379 | `redis` | redis://localhost:6379 |
| 8000 | `backend` | http://localhost:8000/docs |
| 8080 | `airflow-webserver` | http://localhost:8080 |
| 8585 | `openmetadata` | http://localhost:8585 |
| 8888 | `python` | http://localhost:8888 |
| 9000 / 9001 | `minio` | http://localhost:9001 |
| 9090 | `prometheus` | http://localhost:9090 |
| 9200 | `elasticsearch` | http://localhost:9200 |

| Port ไม่ publish (internal) | Service |
|---|---|
| 8080 | `airflow-scheduler`, `airflow-triggerer`, `openmetadata-ingestion` |
| 9100 | `worker`, `scheduler` (metrics เปิดแล้ว) |
| 9187 | `postgres-exporter` |
| 9121 | `redis-exporter` |