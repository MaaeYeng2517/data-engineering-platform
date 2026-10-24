# TEST_PLAN.md

## 1. Objective
กำหนดแผนการทดสอบครอบคลุม Functional, Security, Data Integrity, Performance, Resilience, Backup/Restore และ Audit เพื่อตรวจสอบความพร้อมก่อน Production

## 2. Scope
ครอบคลุม Control API, Web Portal, Data Pipeline, Governance Workflow, RBAC, Lineage, Quality, Audit/Evidence

## 3. Test Levels
| Level | Description | Responsibility |
| --- | --- | --- |
| **Unit** | ทดสอบฟังก์ชัน/โมดูลแยก | Developer |
| **Integration** | ทดสอบการเชื่อมต่อระหว่าง Component | Developer + QA |
| **System** | ทดสอบระบบทั้งหมดแบบ End-to-End | QA + Tech |
| **Security** | SAST/DAST/Dependency/Secret Scan | Security + QA |
| **UAT** | ทดสอบโดยผู้ใช้งานจริง | Business + Data Owner |
| **Acceptance** | ผ่านเกณฑ์ตาม Acceptance Criteria | Business Owner + QA Lead |

## 4. Test Matrix
| Test Type | Objective | Tools (แนะนำ) | Entry Criteria | Exit Criteria | Priority |
| --- | --- | --- | --- | --- | --- |
| **Unit Test** | ตรวจสอบ Logic/Validation | pytest, jest/vitest | Code committed | Coverage >= เป้าหมายที่กำหนด, Critical ผ่าน | P0 |
| **Integration Test** | API + DB + IdP + Storage | pytest + httpx, Postman/Newman | Unit ผ่าน | Workflow หลักผ่านครบ | P0 |
| **RBAC Test** | ทดสอบสิทธิ์ทุกบทบาท | Automated + Manual | RBAC Matrix พร้อม | ไม่มี Unauthorized Access ที่ยืนยันได้ | P0 |
| **Tenant/Scope Isolation** | ป้องกันข้าม Org/Domain/Dataset | Manual + Automated | Isolation Design พร้อม | ปฏิเสธทุกกรณีที่ไม่อนุญาต | P0 |
| **Data Quality** | Null/Duplicate/Schema Drift/Referential | Great Expectations/Soda | Rules กำหนดแล้ว | Critical Rules ผ่าน | P0 |
| **Data Lineage** | Traceability Source→Target | Manual Verification | Pipeline ทำงาน | Lineage ครบสำหรับ Dataset สำคัญ | P0 |
| **Approval Workflow** | SoD, Submit/Approve/Publish | E2E Test | Workflow พร้อม | Self-Approval ไม่ได้, Audit บันทึก | P0 |
| **Security Test** | Vuln/Config/Secrets | Trivy, Semgrep, Gitleaks, OWASP ZAP | Build เสร็จ | ไม่มี Critical/High ที่ยังไม่แก้ไขหรือไม่อนุมัติ | P0 |
| **API Security** | AuthN/AuthZ/IDOR/Rate Limit | OWASP ZAP/Postman | API Spec พร้อม | ผ่าน Security Checks หลัก | P0 |
| **Performance Test** | Load/Stress/Spike | k6/JMeter | Staging พร้อมข้อมูลจำลอง | ผ่าน SLA/SLO ที่อนุมัติ | P1 |
| **Resilience Test** | Failure/Retry/Timeout | Chaos-lite/Manual | Infra พร้อม | กู้คืนได้ ไม่สูญเสียข้อมูล | P1 |
| **Backup/Restore Test** | PITR + Object Restore | Manual Runbook-based | Backup พร้อม | ผ่าน RPO/RTO ที่กำหนด | P0 |
| **Audit Test** | Traceability เหตุการณ์ | Manual Review | Audit Enabled | เหตุการณ์สำคัญเชื่อมโยงได้, Immutable | P0 |
| **UAT** | Business Validation | UAT Scripts | System Test ผ่าน | Business Owner อนุมัติลายลักษณ์อักษร/Email | P0 |

## 5. Acceptance Test Cases (Detailed)
| Test ID | Title | Precondition | Steps | Expected Result | Priority | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| **AT-01** | Access Control by Role | ผู้ใช้ Sales, Dataset Restricted | พยายาม GET /datasets/{restricted_id} | HTTP 403 + Error Code DATASET_ACCESS_DENIED, ไม่มีข้อมูลรั่วไหล | P0 | Request/Response, Audit Log |
| **AT-02** | SoD - Self Approval | Data Owner พยายาม Approve Dataset ที่ตนเอง Submit | POST /datasets/{id}/approve | HTTP 403 หรือระบบปฏิเสธ, บันทึกใน Audit | P0 | Workflow Log, Audit Event |
| **AT-03** | Data Lineage Traceability | Pipeline ทำงานสำเร็จ | GET /datasets/{id}/lineage | แสดง Source → Transform → Target ครบ, ระบุ Pipeline/Version | P0 | Lineage Graph Screenshot/JSON |
| **AT-04** | Data Quality Gate | ข้อมูลไม่ผ่าน Critical Rule | Trigger Pipeline | Pipeline Block/Quarantine, แจ้งผู้รับผิดชอบ, ไม่ Publish | P0 | Quality Results, Notification Log |
| **AT-05** | Approval Workflow | Dataset Draft | Submit → Approve โดยผู้มีสิทธิ์ | สถานะเปลี่ยน draft→pending→published, ทุกขั้นบันทึก Audit | P0 | Status History, Audit Trail |
| **AT-06** | Audit Immutability | พยายามแก้ไข Audit Log | ลองแก้ไข/ลบผ่าน API/DB | ปฏิเสธ, บันทึกความพยายาม, สิทธิ์จำกัด | P0 | Access Log, DB Permission Check |
| **AT-07** | Backup Restore | กู้คืนจาก Snapshot/PITR | ทำตาม Restore Runbook | ข้อมูลคืนค่าได้, Integrity Check ผ่าน, RTO/RPO ตรงตามเป้าหมาย | P0 | Restore Report (EV-006) |
| **AT-08** | Column Masking | ผู้ใช้ไม่มีสิทธิ์ดู PII | Query ข้อมูลที่มี PII | คอลัมน์ PII ถูก Mask เช่น ****/XXX | P0 | Query Result, Policy Check |
| **AT-09** | Idempotency | เรียก POST ซ้ำด้วย Idempotency-Key เดียวกัน | POST /pipelines/{id}/runs ซ้ำ | คืนผลเดียวกัน ไม่สร้าง Run ซ้ำ | P0 | Request Logs |
| **AT-10** | Correlation ID Traceability | เกิด Error | ตรวจสอบ Logs | สามารถ Trace Cross-Service ด้วย Correlation ID | P0 | Log Correlation |

## 6. Test Environment
| Environment | Config | Data | Notes |
| --- | --- | --- | --- |
| **Unit/Dev** | Mock/Local DB | Synthetic Data | เร็ว, ไม่กระทบระบบอื่น |
| **Integration** | Staging Config | Anonymized/Synthetic | ใกล้เคียง Prod มากที่สุด |
| **Staging** | Mirror Prod Config | Anonymized Data | ใช้สำหรับ System/Security/UAT |
| **Prod** | Production | Real Data | **ห้าม** รัน destructive test โดยไม่อนุมัติ |

## 7. Defect Management
| Severity | Definition | SLA (แก้ไข) | Action |
| --- | --- | --- | --- |
| **Critical (S1)** | Security Breach/ข้อมูลสูญหาย/ระบบหลักล่ม | ทันที | หยุด Release, Escalate, RCA |
| **High (S2)** | ฟังก์ชันสำคัญเสียหาย/สิทธิ์ผิดพลาด | ภายใน 24–48 ชั่วโมง | แก้ไขก่อน Release |
| **Medium (S3)** | ฟังก์ชันรองเสียหาย | ภายใน 3–5 วันทำการ | พิจารณารวม Release หรือ Plan ถัดไป |
| **Low (S4)** | UI/Typo/Minor | ตาม Backlog | จัดลำดับตามความสำคัญ |

## 8. Test Evidence Requirements
ทุก Test Run ต้องเก็บ:
- **Test Plan/Script** – Version ที่ใช้
- **Test Results** – Pass/Fail, % ผ่าน
- **Screenshots/Logs** – สำหรับ Manual Test
- **Automation Reports** – HTML/XML/JUnit
- **Defect Reports** – พร้อม Traceability
- **Sign-off** – โดยผู้มีอำนาจอนุมัติ

เก็บใน `compliance/12_internal_audit/` หรือ `tests/reports/` ตามนโยบายเอกสาร

## 9. Entry/Exit Criteria Summary
| Phase | Entry | Exit |
| --- | --- | --- |
| **System Test** | Integration ผ่าน, Build ผ่าน Scan | Test Matrix ผ่าน, Critical/High ไม่มีค้าง |
| **Security Test** | System Test เริ่มได้ | ไม่มี Critical/High ที่เปิดค้าง หรือมี Exception ที่อนุมัติ |
| **UAT** | Security Test ผ่านเกณฑ์ | UAT Sign-off โดย Business/Data Owner |
| **Go-Live Readiness** | UAT ผ่าน, Backup/Restore ทดสอบแล้ว, Runbook พร้อม | Stage Gate ผ่านครบทุก Gate, Management Review อนุมัติ |

## 10. Roles & Responsibilities
| Role | Responsibility |
| --- | --- |
| **QA Lead** | วางแผน, ควบคุม, รวบรวม Evidence, Sign-off |
| **Testers/QA** | ดำเนินการทดสอบ, รายงาน Defect |
| **Developers** | แก้ไข Defect, Unit/Integration Test |
| **Security Lead** | Security Test & Review |
| **Data Owners/Stewards** | UAT, Data Acceptance |
| **Platform/Infra** | Backup/Restore, Resilience Test |
| **Internal Auditor** | ตรวจสอบความเป็นอิสระของ Evidence |

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Review | **ผู้รับผิดชอบ:** QA Lead
