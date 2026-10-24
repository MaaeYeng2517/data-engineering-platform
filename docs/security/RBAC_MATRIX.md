# RBAC_MATRIX.md

## 1. Objective
กำหนดบทบาท, สิทธิ์, ขอบเขต (Scope) และหลักการแยกหน้าที่ (Separation of Duties) สำหรับ Enterprise Data Platform

## 2. Core Principles
- **Deny by Default** – ปฏิเสธหากไม่มีสิทธิ์
- **Least Privilege** – ให้เท่าที่จำเป็น
- **Need-to-Know** – จำกัดตามข้อมูลที่จำเป็น
- **Separation of Duties** – ผู้ร้องขอไม่อนุมัติของตนเอง
- **Scope-based Access** – จำกัดตาม Organization/Domain/Dataset
- **Time-bound / Reviewable** – มีอายุและทบทวน

## 3. Role Definitions
| Role | Type | Description | Typical Users |
| --- | --- | --- | --- |
| **platform_admin** | Privileged | ดูแลแพลตฟอร์ม, Config, Infra-level | Platform/DevOps Lead |
| **security_admin** | Privileged | Security Policy, IAM, Incident, Audit Config | Security Lead |
| **data_governance_lead** | Governance | กำกับดูแล Governance, Classification, Policy | Governance Lead |
| **data_owner** | Business Owner | รับผิดชอบข้อมูลในโดเมน, อนุมัติการเผยแพร่/การเข้าถึง | Domain Head |
| **data_steward** | Governance Ops | ดูแล Metadata, Glossary, Quality, ช่วย Data Owner | Domain Steward |
| **data_engineer** | Technical | สร้าง/ดูแล Pipeline, Transformation | Data/Analytics Engineer |
| **data_analyst** | Consumer | Query Data Product ที่อนุมัติ | Analyst/BI User |
| **business_user** | Consumer | ใช้ Dashboard/Data Product | Business User |
| **auditor** | Read-Only | ตรวจสอบ Audit/Evidence เท่านั้น | Internal/External Auditor |
| **service_account** | Machine | เรียกใช้ API/Job อัตโนมัติ | CI/CD, Pipelines |

## 4. Permission Matrix (Resource:Action)
**สัญลักษณ์:** `✓` = อนุญาต (ตาม Scope), `A` = ต้องอนุมัติ, `R` = Read-only, `—` = ไม่อนุญาต

| Resource / Action | platform_admin | security_admin | data_governance_lead | data_owner | data_steward | data_engineer | data_analyst | business_user | auditor | service_account |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **platform:config:read** | ✓ | R | — | — | — | — | — | — | R | — |
| **platform:config:update** | ✓* | A* | — | — | — | — | — | — | — | — |
| **users:read** | ✓* | ✓ | — | — | — | — | — | — | R | — |
| **users:manage** | ✓* | A* | — | — | — | — | — | — | — | — |
| **roles:assign** | ✓* | A* | — | — | — | — | — | — | — | — |
| **domains:read** | ✓ | ✓ | ✓ | ✓ (own) | ✓ (own) | ✓ | ✓ | R | R | R |
| **domains:manage** | — | — | ✓* | A* | — | — | — | — | — | — |
| **datasets:read** | ✓* | R* | ✓ | ✓ (own) | ✓ (own) | ✓ (allowed) | ✓ (approved) | ✓ (approved) | R | ✓ (scoped) |
| **datasets:create** | — | — | ✓* | ✓ | ✓ | ✓ | — | — | — | ✓* |
| **datasets:update** | — | — | ✓* | ✓ (own) | ✓ (own) | ✓ (own draft) | — | — | — | — |
| **datasets:submit** | — | — | — | ✓ (own) | ✓ (own) | ✓ (own) | — | — | — | — |
| **datasets:approve** | — | — | A* | A (own domain) | — | — | — | — | — | — |
| **datasets:publish** | — | — | ✓* | A | — | — | — | — | — | — |
| **pipelines:read** | ✓* | R* | ✓ | ✓ (own) | ✓ | ✓ | R | — | R | ✓ |
| **pipelines:create/update** | — | — | — | — | — | ✓ (own) | — | — | — | — |
| **pipelines:execute** | — | — | — | — | — | ✓ (own) | — | — | — | ✓ (scoped) |
| **quality:rules:manage** | — | — | ✓* | ✓ (own) | ✓ (own) | ✓ (assist) | — | — | — | — |
| **quality:results:read** | ✓* | R* | ✓ | ✓ (own) | ✓ (own) | ✓ | ✓ (related) | — | R | ✓ |
| **lineage:read** | ✓* | R* | ✓ | ✓ (own) | ✓ (own) | ✓ | ✓ (approved) | ✓ (approved) | R | ✓ |
| **approvals:read** | ✓* | R* | ✓ | ✓ (inbox) | ✓ | ✓ | — | — | R | — |
| **approvals:decide** | — | — | ✓* | A (own) | — | — | — | — | — | — |
| **audit:read** | ✓* | ✓ | R* | R (own scope) | R (own scope) | R (own scope) | — | — | ✓ (read-only) | — |
| **evidence:read** | ✓* | ✓ | ✓* | R (relevant) | R (relevant) | — | — | — | ✓ (read-only) | — |
| **evidence:manage** | — | A* | A* | — | — | — | — | — | — | — |

\* = ต้องมี Scope ชัดเจน + ผ่านการตรวจสอบ/อนุมัติ, ห้ามให้สิทธิ์แบบ `*` ทั่วทั้งระบบโดยไม่จำกัด

## 5. Data-Level Security
| Control | Description | 적용 |
| --- | --- | --- |
| **Column Masking** | ซ่อน/มาสก์คอลัมน์ที่มีความอ่อนไหว (PII, Salary) | ตาม Classification + Role |
| **Row Filtering (RLS)** | จำกัดแถวตาม Domain/Tenant/Org | ทุก Query ผ่าน Gateway |
| **Export Restrictions** | จำกัด Export CSV/Excel/PDF สำหรับ Restricted | ตาม Role + Approval |
| **Query Limits** | จำกัดจำนวนแถว/Timeout | ป้องกัน Bulk Download |
| **PII Tagging** | Tag PII ใน Metadata | บังคับสำหรับ Restricted |

## 6. Privileged Access Management (PAM)
| Requirement | Implementation |
| --- | --- |
| **MFA Mandatory** | บังคับ MFA สำหรับ Privileged Roles |
| **Just-in-Time (JIT)** | ขอสิทธิ์ชั่วคราว + Approval + Time Limit |
| **Session Recording/Logging** | บันทึกทุก Session ของ Privileged Account |
| **Break-Glass** | Emergency Account แยกต่างหาก, ใช้ต้องรายงานทันที |
| **Access Review** | ทบทวน Privileged Access รายไตรมาส |
| **Credential Rotation** | หมุนเวียนตามนโยบาย |

## 7. Separation of Duties Matrix
| Function | Forbidden Combination | Rationale |
| --- | --- | --- |
| **Create + Approve Dataset** | data_engineer + data_owner (same person) | ป้องกัน Self-Approval |
| **Request + Approve Access** | requester + approver (same person) | ป้องกันการอนุมัติสิทธิ์ตนเอง |
| **Dev + Prod Access** | developer ใน prod โดยไม่ผ่าน JIT/Approval | ป้องกัน Uncontrolled Change |
| **Audit + Operations** | auditor + platform_admin/engineer | ความเป็นอิสระของการตรวจสอบ |
| **Security Config + Data Ops** | security_admin + data_engineer ที่มีสิทธิ์สูงเกินจำเป็น | ลดความเสี่ยงการหลบหลีก Control |

## 8. Service Account Governance
| Control | Requirement |
| --- | --- |
| **Ownership** | แต่ละ Service Account ต้องมี Owner ที่รับผิดชอบ |
| **Least Privilege** | จำกัดเฉพาะ Resource/Action ที่จำเป็น |
| **No Interactive Login** | ห้ามใช้สำหรับ Login ผ่าน UI |
| **Secret Rotation** | หมุนเวียนตามรอบที่กำหนด |
| **Usage Monitoring** | ติดตามการใช้งานและแจ้งเตือนผิดปกติ |
| **Lifecycle** | สร้าง-อนุมัติ-ใช้งาน-เพิกถอน มี Audit |

## 9. Access Recertification
| Frequency | Scope | Responsible |
| --- | --- | --- |
| **Monthly** | Privileged Accounts | Security Admin + IAM Lead |
| **Quarterly** | All User Roles | Data Governance Lead + System Owners |
| **On Event** | Joiner/Mover/Leaver, Project End | HR + Security + Data Owners |
| **Ad-hoc** | Incident/Policy Change | Security Lead |

ผลการทบทวนต้องบันทึกใน `Access Review Report` และเก็บเป็นหลักฐาน

## 10. Implementation Checklist
- [ ] IdP Integration (OIDC/SAML) + MFA
- [ ] RBAC Engine with Scope Enforcement
- [ ] Policy Decision Point (PDP)/Enforcement Point (PEP)
- [ ] RLS + Column Masking
- [ ] Audit Logging for all AuthZ/AuthN
- [ ] Approval Workflow with SoD
- [ ] JIT/PAM for Privileged
- [ ] Access Review Automation
- [ ] Service Account Registry

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Review | **ผู้รับผิดชอบ:** Security Lead & IAM Lead
