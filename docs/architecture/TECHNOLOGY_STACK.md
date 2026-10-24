# TECHNOLOGY_STACK.md

## 1. Objective
ระบุเทคโนโลยีที่เลือกใช้, เหตุผล, ข้อพิจารณา และทางเลือก (Alternatives) สำหรับ Enterprise Data Platform

## 2. Stack Overview
| Layer | Technology | Version (แนะนำ) | Type | Rationale |
| --- | --- | --- | --- | --- |
| **Frontend** | Next.js, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query | Next.js 14.x | Open Source | SSR/App Router, Type-safe, Component System, DX ดี |
| **Backend/API** | FastAPI, Pydantic v2, Uvicorn/Gunicorn | FastAPI >=0.110 | Open Source | Async, Auto Docs, Validation, Performance ดี |
| **Identity Provider** | Keycloak (หรือ Enterprise SSO: Entra ID/Okta) | Keycloak 24.x+ | Open Source/Enterprise | OIDC/SAML, MFA, RBAC, Federation |
| **API Gateway** | NGINX/Kong/Traefik | ตามการใช้งาน | Open Source | Routing, TLS, Rate Limit, AuthZ |
| **Metadata DB** | PostgreSQL | 16.x | Open Source | ACID, JSONB, RLS, Mature, ทีมคุ้นเคย |
| **Cache/Broker** | Redis | 7.x | Open Source | Cache, Session, Celery Broker |
| **Task Queue** | Celery | 5.x | Open Source | Async Jobs, Retry, Scheduling |
| **Object Storage** | MinIO / AWS S3 / Azure Blob | S3 Compatible | Open Source/Managed | Scalable, Versioning, Lifecycle |
| **Lakehouse Format** | Apache Iceberg + Parquet | Iceberg 1.x | Open Source | Schema Evolution, Time Travel, Interoperable |
| **Query Engine** | Trino | 450+ | Open Source | Federated SQL, Performance ดี |
| **Orchestration** | Apache Airflow | 2.9+ | Open Source | DAGs, Dependencies, SLA, Observability |
| **Transformation** | dbt Core | 1.8+ | Open Source | SQL-first, Testing, Docs, Version Control |
| **Data Quality** | Great Expectations / Soda Core | ตามเวอร์ชัน | Open Source | Expectations, Validation, Data Docs |
| **Data Catalog/Lineage** | OpenMetadata | 1.4+ | Open Source | Catalog, Ownership, Lineage, Glossary |
| **BI/Visualization** | Apache Superset / Metabase | ล่าสุดที่เสถียร | Open Source | Dashboards, RBAC, SQL Lab |
| **Secrets** | HashiCorp Vault / Cloud Secrets Manager | ตามที่ใช้งาน | Open Source/Managed | Centralized, Rotation, Audit |
| **IaC** | Terraform | 1.9+ | Open Source | Reproducible, State Management |
| **Containerization** | Docker, Docker Compose/Kubernetes | ตามสภาพแวดล้อม | Open Source | Portability, Isolation |
| **CI/CD** | GitHub Actions / GitLab CI | N/A | SaaS/On-Prem | Build/Test/Scan/Deploy |
| **Observability** | Prometheus, Grafana, OpenTelemetry, Loki/ELK | เสถียร | Open Source | Metrics/Logs/Traces |
| **Security Scanning** | Trivy, Gitleaks, Semgrep, Grype | ล่าสุดที่เสถียร | Open Source | SAST/SCA/Secret/Image Scan |

## 3. Selection Criteria
| เกณฑ์ | น้ำหนัก | คำอธิบาย |
| --- | --- | --- |
| **Maturity & Community** | 20% | มีการใช้งานจริง, อัปเดตสม่ำเสมอ |
| **Security** | 20% | มีการพัฒนาเรื่องความปลอดภัย, รองรับ Best Practice |
| **Operability** | 15% | ดูแลง่ายสำหรับทีมขนาดกลาง |
| **Interoperability** | 15% | เปิดมาตรฐาน, ไม่ Lock-in มากเกินไป |
| **Cost (TCO)** | 10% | License + Infra + Ops + Training |
| **Ecosystem/Integration** | 10% | เข้ากันได้กับระบบเดิม |

## 4. Rationale per Critical Component
| Component | เหตุผล |
| --- | --- |
| **PostgreSQL** | เหมาะกับ Metadata/Control, รองรับ JSONB + RLS, มีประวัติความปลอดภัยดี |
| **FastAPI** | เหมาะกับ API ที่เน้น Validation + Security + Documentation |
| **Airflow** | เหมาะกับ Data Orchestration ที่ซับซ้อน มี SLA/Retry/Alerting |
| **dbt** | ส่งเสริม SQL-first, Version Control, Testing, Data Contracts |
| **Iceberg** | ช่วยให้ Lakehouse ยืดหยุ่น รองรับ Schema Evolution/Time Travel |
| **OpenMetadata** | ครอบคลุม Catalog+Lineage+Glossary+Ownership ในเครื่องมือเดียว |
| **Keycloak** | ครบถ้วนสำหรับ Enterprise IAM โดยไม่ต้องพึ่ง SaaS ทันที |

## 5. Alternatives Considered
| Category | Primary | Alternative | หมายเหตุ |
| --- | --- | --- | --- |
| **Orchestration** | Airflow | Dagster, Prefect | Dagster ดีแต่ทีมต้องเรียนรู้ใหม่มากขึ้น |
| **Catalog** | OpenMetadata | DataHub, Atlan | DataHub แข็งแรงแต่ Operability อาจซับซ้อนกว่า |
| **Query** | Trino | Presto, DuckDB | DuckDB เหมาะกับ Small/Ad-hoc ไม่ครอบคลุม Federated ขนาดใหญ่เท่า Trino |
| **Quality** | Great Expectations | Soda Core, Monte Carlo | Soda Core ใช้งานง่าย, Great Expectations ครอบคลุมกว้างกว่า |

## 6. Security & Compliance Considerations
- **SBOM** – พิจารณาสร้าง SBOM สำหรับ Image/Dependency
- **Image Hardening** – ใช้ Distroless/Minimal Base Image
- **Secrets** – ห้าม Hardcode, ใช้ Vault/Secrets Manager
- **Network** – Private Subnet, NAT Gateway แบบจำกัด
- **TLS** – บังคับ TLS ทุกจุด
- **Logging** – ไม่ log PII/Secret
- **Patching** – มีแผน Patch Management

## 7. Deployment Model Recommendation
| Scenario | Recommendation |
| --- | --- |
| **เริ่มต้น (On-Prem + Cloud Hybrid)** | Docker Compose / VM + Kubernetes (ถ้ามีทีม DevOps เพียงพอ) |
| **ต้องการลด Ops** | ใช้ Managed DB/Object Storage + Self-hosted Control Plane |
| **เน้น ISO Readiness** | เน้น Traceability, Audit, Evidence มากกว่าใช้ Trendy Stack |

## 8. Approval
| Role | Name/Signature | Date |
| --- | --- | --- |
| Solution Architect | ___________ | ____/____/____ |
| Security Lead | ___________ | ____/____/____ |
| Platform Lead | ___________ | ____/____/____ |

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Review
