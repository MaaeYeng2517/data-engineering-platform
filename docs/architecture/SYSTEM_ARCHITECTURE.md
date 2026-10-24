# SYSTEM_ARCHITECTURE.md

## 1. Objective
ออกแบบ Enterprise Data Platform สำหรับองค์กรขนาด 100–500 คน บนสถาปัตยกรรม Hybrid Cloud โดยยึดหลัก Governance by Design, Security by Design, Auditability by Design เพื่อใช้เป็นศูนย์กลางการจัดการข้อมูลและเตรียมความพร้อมสู่ ISO/IEC 27001:2022

## 2. Scope
- ครอบคลุม Ingestion, Storage, Transformation, Catalog, Lineage, Quality, Governance, Access Control, Audit, Monitoring
- รองรับทั้ง On-Premises และ Cloud
- เน้นการควบคุมข้อมูลที่มีความอ่อนไหวและหลักฐานการตรวจสอบย้อนกลับ
- ไม่รวมการพัฒนาระบบ ERP/CRM ภายในแต่ครอบคลุมการเชื่อมต่อ

## 3. Architecture Principles
| หลักการ | คำอธิบาย |
| --- | --- |
| **Zero Trust** | ไม่เชื่อถือเครือข่ายภายใน, ตรวจสอบตัวตนและสิทธิ์ทุกครั้ง |
| **Least Privilege** | ให้สิทธิ์เท่าที่จำเป็นต่อการทำงาน |
| **Deny by Default** | ปฏิเสธการเข้าถึงหากไม่มีนโยบายอนุญาต |
| **Separation of Duties (SoD)** | แยกหน้าที่ระหว่างผู้ร้องขอ-ผู้อนุมัติ-ผู้ตรวจสอบ |
| **Secure by Default** | เปิดใช้งานการเข้ารหัส, Audit, MFA โดยค่าเริ่มต้น |
| **Immutable Audit** | บันทึกเหตุการณ์สำคัญไม่สามารถแก้ไขได้โดยผู้ไม่มีสิทธิ์พิเศษ |
| **Data Minimization** | เก็บ/ส่งข้อมูลเท่าที่จำเป็นต่อวัตถุประสงค์ที่ได้รับอนุมัติ |

## 4. Hybrid Cloud Topology
```text
[Enterprise Users] -> [IdP/SSO + MFA] -> [API Gateway/WAF]
                        |                        |
                    [VPN/Private Link]      [Public Edge (Filtered)]
                        |                        |
                    On-Prem Zone            Cloud Zone
                  (Systems, Agents)      (Workers, Lakehouse, BI)
                        \                        /
                         \                      /
                          \                    /
                           [Enterprise Data Control Plane]
                                     |
                               [Data Products / APIs / AI]
```

## 5. Planes Architecture
| Plane | วัตถุประสงค์ | องค์ประกอบหลัก |
| --- | --- | --- |
| **Control Plane** | ควบคุมสิทธิ์, นโยบาย, Metadata, การอนุมัติ | FastAPI, PostgreSQL (Metadata), Keycloak/IdP, Policy Engine |
| **Data Plane** | ประมวลผล, แปลง, จัดเก็บข้อมูล | Airflow, dbt, Workers, Object Storage, Iceberg, Trino |
| **Security Plane** | การปกป้องและการตอบสนอง | IAM, KMS, Network Controls, WAF, IDS/IPS, Secrets Manager |
| **Observability Plane** | การตรวจสอบและการแจ้งเตือน | Prometheus, Grafana, OpenTelemetry, Log Aggregation |
| **Consumption Plane** | การให้บริการข้อมูล | SQL Gateway, REST API, BI (Superset/Metabase), AI/RAG |

## 6. Network Zones
| Zone | จุดประสงค์ | การควบคุม |
| --- | --- | --- |
| **User** | การเข้าถึงของผู้ใช้งาน | SSO, MFA, Session Management, Rate Limit |
| **Application** | บริการภายใน (API, Portal) | Service-to-Service Auth, mTLS/TLS, Network Policy |
| **Data Processing** | งาน ETL/ELT/Quality | Isolated Workers, Least Privilege, No Direct Internet |
| **Storage** | Object/Lakehouse/DB | Encryption, Bucket Policy, VPC/Private Endpoint |
| **Management** | Admin/CI-CD/Bastion | Jump Host/Bastion, MFA, Approval, Session Logging |
| **Logging/Audit** | เก็บ Audit Logs | แยกระบบ, Immutable Storage, Restricted Access |
| **Recovery** | กู้คืนระบบเมื่อเกิดเหตุ | แยก Credential, Air-Gapped-like Access, Controlled Workflow |

## 7. Data Flow Overview
1. **Connect** – เชื่อมต่อแหล่งข้อมูลผ่าน Connector ที่ได้รับอนุญาต
2. **Ingest** – นำเข้าด้วย Idempotent + Checksum + Schema Validation
3. **Register** – ลงทะเบียนใน Data Catalog พร้อม Owner/Classification
4. **Transform** – แปลงด้วย dbt ภายใต้ Version Control
5. **Validate** – ตรวจสอบคุณภาพด้วย Data Quality Rules
6. **Lineage** – บันทึกความสัมพันธ์ Source→Transform→Target
7. **Publish** – ขออนุมัติและเผยแพร่เป็น Certified Data Product
8. **Consume** – เข้าถึงผ่าน API/SQL/BI ตามสิทธิ์
9. **Audit** – บันทึกทุกกิจกรรมที่มีผลต่อการเข้าถึง/อนุมัติ

## 8. Security Architecture
| ด้าน | มาตรการ |
| --- | --- |
| **Identity** | OIDC/SAML, MFA, Conditional Access, Session Timeout |
| **Authorization** | RBAC + Scope-based, Policy-as-Code, ABAC ในกรณีที่จำเป็น |
| **Encryption** | TLS 1.3 (Transit), AES-256 (At-Rest), Key Rotation, HSM/KMS |
| **Secrets** | Secrets Manager/Vault, ไม่มี Secret ใน Repo/Log |
| **Network** | Segmentation, Private Endpoints, Firewall, egress control |
| **Logging** | Structured Logging, Correlation ID, Central Log, Tamper-evident |
| **Vulnerability** | SAST/DAST/SCA/Image Scan, Dependency Review |
| **Incident** | Incident Response Plan, Escalation Matrix, Post-Incident Review |

## 9. High Availability & Resilience
- **Stateless Services** – Scale horizontally
- **Database** – Replication + PITR
- **Object Storage** – Versioning + Lifecycle
- **Orchestration** – Retry/Backoff/Idempotency
- **Health Checks** – Liveness/Readiness
- **Graceful Shutdown** – ป้องกันงานค้าง
- **DR Ready** – Runbook + Tested Restore

## 10. Architecture Decision Records (ADR) Guidelines
ทุกการตัดสินใจสำคัญต้องบันทึกใน `docs/architecture/adr/` โดยมี: Context, Decision, Consequences, Status, Date, Author

## 11. Review & Approval
| บทบาท | หน้าที่ |
| --- | --- |
| **Solution Architect** | อนุมัติสถาปัตยกรรมโดยรวม |
| **Security Lead** | ตรวจสอบความมั่นคงปลอดภัย |
| **Data Governance Lead** | ตรวจสอบ Governance Alignment |
| **Platform Lead** | ตรวจสอบ Operational Feasibility |

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Review | **วันที่:** 2025-10-24
