# IMPLEMENTATION_ROADMAP.md

## 1. Objective
แผนการดำเนินงาน 8 เดือน พร้อม Phase, Deliverables, Stage Gates, ทีมงาน และความเสี่ยงหลัก

## 2. Overall Timeline
| Phase | เดือน | Focus | Status |
| --- | --- | --- | --- |
| **Phase 1** | เดือน 1 | Assessment & ISO Gap Analysis | Planned |
| **Phase 2** | เดือน 2 | Hybrid Infrastructure Foundation | Planned |
| **Phase 3** | เดือน 3 | Core Control Plane (RBAC/Catalog/Approval) | Planned |
| **Phase 4** | เดือน 4 | Data Ingestion & Lakehouse | Planned |
| **Phase 5** | เดือน 5 | Governance, Quality, Lineage | Planned |
| **Phase 6** | เดือน 6 | Analytics & Business Adoption (UAT) | Planned |
| **Phase 7** | เดือน 7 | Security, Ops Validation, Evidence | Planned |
| **Phase 8** | เดือน 8 | Internal Audit & Certification Readiness | Planned |

## 3. Detailed Roadmap
### Phase 1: Assessment & ISO Gap Analysis (เดือน 1)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Stakeholder Mapping** | PM/BA | 2–3 วัน | Stakeholder Register | อนุมัติโดยผู้บริหาร |
| **ISMS Scope Definition** | ISMS Lead | 3–4 วัน | ISMS Scope Statement | อนุมัติ & ลงนาม |
| **Current State Assessment** | Solution Architect | 4–5 วัน | As-Is Assessment | ครอบคลุมระบบหลัก |
| **ISO Gap Analysis** | ISMS Lead + Security | 5–7 วัน | Gap Analysis Report | ระบุ Gap + Priority |
| **Risk Assessment Kickoff** | Risk Owner | 2–3 วัน | Risk Register Draft | มี Risk Register เบื้องต้น |

**Deliverables:** Scope, Risk Register, Target Architecture, ADRs

### Phase 2: Hybrid Infrastructure Foundation (เดือน 2)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Network Design & Segmentation** | Network/Platform | 5–7 วัน | Network Diagram + Policy | ผ่าน Security Review |
| **VPN/Private Connectivity** | Network/Platform | 3–5 วัน | Connectivity Tested | ทดสอบเรียบร้อย |
| **IAM/MFA/SSO Setup** | IAM Lead | 4–5 วัน | IdP Integration | MFA บังคับใช้งาน |
| **Secrets Management** | Security/Platform | 2–3 วัน | Vault/Secrets Manager | ไม่มี Secret ใน Repo |
| **CI/CD Pipeline** | DevOps | 4–5 วัน | CI/CD with Scans | Build/Test/Scan ทำงาน |
| **Logging/Monitoring Baseline** | Obs Lead | 3–4 วัน | Prometheus/Grafana/Loki | Alerts เบื้องต้น |
| **Backup Baseline** | Infra Lead | 2–3 วัน | Backup Config | ทดสอบครั้งแรก |

**Deliverables:** Infrastructure Baseline, IAM, Deployment Pipeline

### Phase 3: Core Control Plane (เดือน 3)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Control API Setup** | Backend Lead | 5–7 วัน | FastAPI Core + AuthZ | AuthN/AuthZ ทำงาน |
| **Metadata DB & Migrations** | Backend/DBA | 4–5 วัน | PostgreSQL Schema + Alembic | Migrations ผ่าน |
| **Users/Roles/Permissions** | IAM Lead + Backend | 4–5 วัน | RBAC Engine | ตาม RBAC Matrix |
| **Data Catalog Registry** | Data Governance | 4–5 วัน | Catalog API/UI | CRUD + Classification |
| **Approval Workflow** | Backend + Governance | 3–5 วัน | Submit/Approve/Reject | SoD บังคับใช้ |
| **API Tests** | QA | 2–3 วัน | API Test Suite | Critical ผ่าน |

**Deliverables:** Core API, RBAC, Metadata Registry

### Phase 4: Data Ingestion & Lakehouse (เดือน 4)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Source Connectivity (Pilot)** | Data Engineer | 4–5 วัน | Connectors | ทดสอบเชื่อมต่อสำเร็จ |
| **Ingestion Pipeline** | Data Engineer | 5–7 วัน | Airflow DAGs | Idempotent + Retry |
| **Object Storage + Iceberg** | Data Engineer/Platform | 4–5 วัน | Lakehouse Setup | Schema Evolution OK |
| **Transformation (dbt)** | Data Engineer | 4–5 วัน | dbt Models + Tests | dbt test ผ่าน |
| **Schema Validation** | Data Engineer | 2–3 วัน | Validation Rules | ป้องกัน Schema Drift |
| **Operational Monitoring** | Obs Lead | 2–3 วัน | DAG/Job Monitoring | Alerts ทำงาน |

**Deliverables:** Data Pipeline, Storage, Operational Monitoring

### Phase 5: Governance, Quality, Lineage (เดือน 5)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Data Dictionary & Glossary** | Data Steward | 3–4 วัน | Glossary in Catalog | ครอบคลุม Domain สำคัญ |
| **Data Classification** | Data Governance | 2–3 วัน | Classification Applied | ทุก Dataset สำคัญมีระดับ |
| **Data Quality Rules** | Data Steward + Engineer | 4–5 วัน | Great Expectations/Soda | Critical Rules ใช้งานได้ |
| **Data Lineage** | Data Engineer + Governance | 4–5 วัน | Lineage Mapping | Source→Target ครบ |
| **Policy Enforcement** | Security + Backend | 3–4 วัน | Policy Engine Integration | บังคับใช้ตาม RBAC/Classification |
| **Retention & Disposal** | Governance + Legal | 2–3 วัน | Retention Policy | กำหนดไว้เป็นลายลักษณ์อักษร |

**Deliverables:** Governance Framework, Quality, Lineage

### Phase 6: Analytics & Business Adoption (เดือน 6)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Certified Data Products** | Data Owner + Engineer | 4–5 วัน | Published Products | ผ่าน Approval Workflow |
| **BI Integration** | BI/Analyst | 4–5 วัน | Superset/Metabase Dashboards | เชื่อมต่อสำเร็จ |
| **Data Access API** | Backend | 3–4 วัน | Consumption API | ตามสิทธิ์ |
| **User Training** | Governance + BA | 3–4 วัน | Training Materials & Sessions | บันทึกการอบรม |
| **UAT Preparation & Execution** | QA + Business | 5–7 วัน | UAT Scripts & Results | Business Owner Sign-off |

**Deliverables:** Business Data Products, BI, UAT Results

### Phase 7: Security, Ops Validation, Evidence (เดือน 7)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Security Testing** | Security + QA | 4–5 วัน | SAST/DAST/Scan Reports | ไม่มี Critical/High ค้าง |
| **Access Control Review** | Security + IAM | 2–3 วัน | Access Review Report | ทำตามรอบ |
| **Performance Testing** | QA + Platform | 3–4 วัน | k6/JMeter Report | ผ่าน SLA/SLO |
| **Resilience Testing** | Platform + QA | 2–3 วัน | Failure Tests | กู้คืนได้ |
| **Backup & Restore Test** | Infra + Security | 3–4 วัน | Restore Test Report (EV-006) | ผ่าน RPO/RTO |
| **Incident Response Drill** | Security | 2–3 วัน | Drill Report | ทีมตอบสนองได้ |
| **Evidence Collection** | ISMS Lead | 4–5 วัน | Evidence Register Updated | ครบตาม Gap Analysis |
| **Runbooks Finalization** | Platform | 2–3 วัน | Complete Runbooks | ผ่าน Review |

**Deliverables:** Test Reports, Recovery Evidence, Operations Runbooks

### Phase 8: Internal Audit & Certification Readiness (เดือน 8)
| Task | Owner | Effort | Deliverable | Done Criteria |
| --- | --- | --- | --- | --- |
| **Pre-Audit Review** | ISMS Lead | 2–3 วัน | Readiness Checklist | ครบทุกข้อ |
| **Internal Audit** | Internal Auditor | 4–5 วัน | Internal Audit Report (EV-008) | ดำเนินการอย่างอิสระ |
| **Corrective Actions** | Process Owners | 3–5 วัน | CAPA Register (EV-010) | แก้ไขจนปิดหรือมีแผนอนุมัติ |
| **Management Review** | Executive Sponsor | 1–2 วัน | Management Review Minutes (EV-009) | อนุมัติผลการทบทวน |
| **Readiness Assessment** | ISMS Lead + Security | 2–3 วัน | Certification Readiness Report | Recommend/Not Recommend |
| **Certification Body Preparation** | ISMS Lead | 2–3 วัน | Scope/SoA/Evidence Package | พร้อมส่งเอกสาร |

**Deliverables:** Audit Report, Corrective Actions, Readiness Assessment

## 4. Stage Gates
| Gate | Criteria | Approver | Required |
| --- | --- | --- | --- |
| **Gate A – Functional** | Features ตาม Requirement, Unit/Integration ผ่าน | Tech Lead + QA Lead | Yes |
| **Gate B – Security** | ไม่มี Critical/High ค้าง หรือมี Exception ที่อนุมัติ | Security Lead | Yes |
| **Gate C – Data Integrity** | Data Quality ผ่าน, Lineage ครบ, Consistent | Data Governance Lead | Yes |
| **Gate D – Operations** | Monitoring, Runbook, Backup, On-Call กำหนดแล้ว | Platform Lead | Yes |
| **Gate E – Compliance** | เอกสาร/หลักฐานครบตาม Phase, SoA อัปเดต | ISMS Lead | Yes |

**กฎ:** ต้องผ่านทุก Gate ก่อนเข้าสู่ Phase ถัดไป

## 5. Resource Plan
| Role | FTE (โดยประมาณ) | Duration | Notes |
| --- | --- | --- | --- |
| **PM/BA** | 1.0 | 8 เดือน | ควบคุมโครงการ |
| **Solution/Data Architect** | 1.0 | 8 เดือน | สถาปัตยกรรม & ADR |
| **Data Engineer** | 2.0 | 6–8 เดือน | Pipeline/Lakehouse |
| **Backend Engineer** | 1–2.0 | 6–8 เดือน | Control API |
| **Frontend Engineer** | 1.0 | 4–6 เดือน | Portal/Dashboard |
| **DevOps/Platform Engineer** | 1.0 | 8 เดือน | Infra/CI-CD/DR |
| **Security/Compliance Specialist** | 1.0 | 7–8 เดือน | Risk/Evidence/ISO |
| **Data Owner/Business SME** | 0.5–0.8 | 6–8 เดือน | Requirements/UAT |
| **Internal Auditor** | 0.3–0.5 | เดือน 7–8 | ตรวจสอบอย่างอิสระ |

## 6. Critical Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| **Scope Creep** | Medium | High | Change Control, Stage Gate บังคับ | PM |
| **ขาดความพร้อมหลักฐาน ISO** | High | High | เก็บ Evidence ตั้งแต่ต้น (Evidence Register) | ISMS Lead |
| **ความซับซ้อน Hybrid Cloud** | Medium | High | Network Design Review, Test Connectivity | Platform Lead |
| **ข้อมูลเสียหายจาก Migration** | Medium | High | Backup ก่อนทุก Migration, Staging Test, Rollback Plan | Platform/DBA |
| **RBAC ผิดพลาด** | High | High | RBAC Test Matrix, SoD Test, Access Review | Security Lead |
| **บุคลากรขาดความรู้** | Medium | High | Training Plan, Pairing, Knowledge Transfer | PM/HR |
| **ผู้ตรวจประเมินเน้น Real Evidence** | High | High | เน้นการดำเนินงานจริง, ไม่สร้างเอกสารปลอม | ISMS Lead |

## 7. Key Milestones
| Milestone | Target | Success Criteria |
| --- | --- | --- |
| **M1: Scope & Risk Approved** | สิ้นเดือน 1 | Scope Statement, Risk Register อนุมัติ |
| **M2: Infrastructure Ready** | สิ้นเดือน 2 | Network/IAM/CI-CD/Monitoring ใช้งานได้ |
| **M3: Control Plane Live** | สิ้นเดือน 3 | RBAC/Catalog/Approval ทำงาน |
| **M4: Data Pipeline Working** | สิ้นเดือน 4 | Ingest/Transform/Load สำเร็จ |
| **M5: Governance Framework Complete** | สิ้นเดือน 5 | Quality/Lineage/Policy ใช้งานได้ |
| **M6: UAT Completed** | สิ้นเดือน 6 | Business Sign-off |
| **M7: Security & Ops Validated** | สิ้นเดือน 7 | Test Reports + Evidence ครบ |
| **M8: Certification Readiness** | สิ้นเดือน 8 | Internal Audit ผ่าน + Mgmt Review อนุมัติ |

## 8. Success Criteria
- **Governance:** ทุก Dataset สำคัญมี Owner/Classification/Lineage
- **Security:** RBAC + MFA + Audit ใช้งานจริง
- **Data Quality:** Critical Rules ผ่านและบันทึกผล
- **Operations:** Runbook ครบ, Backup/Restore ทดสอบแล้ว
- **ISO Readiness:** Evidence Register ครบตาม ISO_COMPLIANCE_MATRIX, Internal Audit ผ่าน, CAPA ติดตามจนใกล้ปิด

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Approval | **ผู้รับผิดชอบ:** Project Manager
