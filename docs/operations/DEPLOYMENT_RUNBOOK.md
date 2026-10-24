# DEPLOYMENT_RUNBOOK.md

## 1. Purpose
คู่มือสำหรับการติดตั้ง, อัปเกรด, Rollback, Backup/Restore และการรับมือเหตุการณ์สำหรับ Enterprise Data Platform

## 2. Prerequisites
- [ ] Access ไปยัง Environment (Dev/Staging/Prod) ตาม Role
- [ ] Secrets พร้อมใช้งานผ่าน Secrets Manager/Vault
- [ ] TLS Certificates
- [ ] Network Access (VPN/Private Link)
- [ ] CI/CD Pipeline พร้อมใช้งาน

## 3. Environment Matrix
| Environment | Purpose | Access | Approval Required |
| --- | --- | --- | --- |
| **dev** | Development | Dev Team | ไม่จำเป็น (ภายใต้ Policy) |
| **staging** | Integration/UAT | QA + Tech + BA | แนะนำให้มี Review |
| **prod** | Production | Restricted (Platform/Security) | ต้องมี Change Approval + CAB/Authorized Approver |

## 4. Deployment Procedure
### 4.1 Pre-Deployment Checklist
- [ ] Change Ticket (EV-007) สร้างและอนุมัติ
- [ ] Build Artifact ผ่าน CI (Lint/Test/Scan)
- [ ] Security Scan ผ่าน หรือมี Exception ที่อนุมัติ
- [ ] Backup สำคัญเสร็จแล้ว
- [ ] Rollback Plan พร้อม
- [ ] Stakeholders แจ้งแล้ว

### 4.2 Backend (Control API)
```bash
# Pull latest
git pull origin main

# Build image
docker build -t enterprise-data-platform/control-api:$(git rev-parse --short HEAD) ./apps/control-api

# Apply migrations
alembic upgrade head

# Deploy
docker compose up -d control-api
# or kubectl apply -f k8s/control-api/
```

### 4.3 Frontend (Web Portal)
```bash
cd apps/web-portal
npm ci
npm run build
npm run start
# หรือ deploy ผ่าน CI/CD
```

### 4.4 Data Platform Services
```bash
# Airflow
docker compose up -d airflow-webserver airflow-scheduler

# Workers
docker compose up -d worker

# dbt (via CI or manual)
dbt deps && dbt run && dbt test
```

### 4.5 Post-Deployment Verification
- [ ] Health Check: `GET /health` และ `GET /ready`
- [ ] Login ผ่าน SSO
- [ ] ทดสอบ RBAC เบื้องต้น
- [ ] ตรวจสอบ Logs/Errors
- [ ] ตรวจสอบ Queue/Jobs
- [ ] ตรวจสอบ Audit Log บันทึกการ Deploy
- [ ] Smoke Test สำคัญ

## 5. Rollback Procedure
1. **แจ้งเตือน** – แจ้ง Stakeholders ทันที
2. **หยุด Traffic** – ถ้าจำเป็น (Maintenance/Blue-Green)
3. **Rollback Image/Artifact** – ใช้ Version ก่อนหน้า
4. **Rollback DB Migration** – ใช้ `alembic downgrade -1` เฉพาะกรณีที่ปลอดภัยและมีแผน
5. **Verify** – Health Check + Smoke Test
6. **Document** – บันทึกใน Change Ticket และ Incident (ถ้ามี)

> **หมายเหตุ:** Migration ที่มีการเปลี่ยน Schema แบบ Destructive ต้องมีแผน Backward Compatible หรือ Downgrade Plan ที่ทดสอบใน Staging แล้ว

## 6. Backup Strategy
| Component | Method | Frequency | Retention | Location |
| --- | --- | --- | --- | --- |
| **PostgreSQL (Control)** | Logical + WAL/PITR | Daily Full + Continuous WAL | ตามนโยบาย (แนะนำ >=30 วัน) | แยกจาก Production |
| **Object Storage** | Versioning + Replication | On-change + Periodic | ตาม Lifecycle Policy | Cross-region/Separate Account |
| **Airflow Metadata** | Included in DB Backup | ร่วมกับ Control DB | ตามนโยบาย | แยก |
| **Configs/Secrets** | Encrypted Backup | ตามการเปลี่ยนแปลง | ตามนโยบาย | Secure Vault/Encrypted Bucket |
| **Evidence/Compliance** | Immutable Backup | รายสัปดาห์/ตามรอบ | ตามข้อกำหนดการตรวจประเมิน | แยกระบบ เข้าถึงจำกัด |

## 7. Restore Procedure
### 7.1 PostgreSQL Restore (PITR)
```bash
# 1. Stop services ที่เชื่อมต่อ DB
# 2. Restore base backup
# 3. Apply WAL logs ถึง Target Time
# 4. Start DB และ Verify integrity
# 5. Run consistency checks
# 6. Start services
```

### 7.2 Object Storage Restore
- ใช้ Versioning เพื่อกู้คืน Object ที่ถูกลบ/แก้ไข
- ใช้ Lifecycle/Replication ตามกรณี

### 7.3 Verification
- [ ] Data Integrity Check
- [ ] Foreign Key/Constraints
- [ ] Application Connectivity
- [ ] User Login
- [ ] Critical Reports
- [ ] Audit Trail ครบถ้วน

**บันทึกผลการ Restore ใน:** `compliance/09_backup_and_recovery/restore-test-YYYY-MM-DD.md`

## 8. Incident Response
### 8.1 Severity Levels
| Level | Definition | Response Time (Target) |
| --- | --- | --- |
| **P0 – Critical** | ระบบหลักล่ม, Data Breach ที่น่าสงสัย | ทันที (24/7) |
| **P1 – High** | ฟังก์ชันสำคัญล้มเหลว, การเข้าถึงไม่ได้รับอนุญาต | ภายใน 1–2 ชั่วโมง |
| **P2 – Medium** | ปัญหาที่ไม่กระทบหลัก | ภายใน 4–8 ชั่วโมง |
| **P3 – Low** | คำถาม/การปรับปรุงเล็กน้อย | ตาม SLA ที่กำหนด |

### 8.2 Response Steps
1. **Detect** – ตรวจพบจาก Alert/รายงาน
2. **Contain** – จำกัดผลกระทบ (Isolate, Revoke Access)
3. **Eradicate** – กำจัดสาเหตุ
4. **Recover** – กลับสู่สถานะปกติ
5. **Post-Incident** – Lessons Learned, RCA, CAPA

### 8.3 Escalation
| Role | Responsibility |
| --- | --- |
| **On-Call Engineer** | First Responder |
| **Security Lead** | Security Incident |
| **Platform Lead** | Technical Escalation |
| **Data Governance Lead** | Governance/Data Related |
| **Executive Sponsor** | P0 ที่มีผลกระทบสำคัญ |

## 9. Monitoring & Alerting
| Metric | Threshold (แนะนำ) | Severity |
| --- | --- | --- |
| **API Error Rate** | > 5% ใน 5 นาที | P1 |
| **DB Connections** | > 80% ของ Pool | P2 |
| **Queue Depth** | > Threshold ที่กำหนด | P2 |
| **Disk Usage** | > 85% | P2 |
| **Memory/CPU** | > 90% | P2 |
| **Failed Login** | ผิดปกติ | P1 |
| **Privilege Escalation** | ผิดปกติ | P0 |
| **Backup Failed** | ไม่สำเร็จ | P1 |

## 10. Security Operations
- **Access Review** – รายไตรมาส
- **Vulnerability Scan** – สม่ำเสมอ
- **Patch Management** – ตามนโยบาย
- **Secret Rotation** – ตามรอบ
- **Log Review** – สม่ำเสมอโดย Security
- **Penetration Test** – ตามแผนที่เหมาะสม

## 11. Contact List
| Role | Contact | Availability |
| --- | --- | --- |
| **Platform Lead** | platform-lead@enterprise.local | On-Call |
| **Security Lead** | security-lead@enterprise.local | On-Call |
| **Data Governance Lead** | dgovernance-lead@enterprise.local | Business Hours + Escalation |
| **DBA/Infra** | infra@enterprise.local | On-Call |

## 12. Appendices
- **Appendix A:** Change Request Template
- **Appendix B:** Incident Report Template
- **Appendix C:** Restore Test Checklist
- **Appendix D:** Access Review Checklist

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Review | **ผู้รับผิดชอบ:** Platform Lead & Security Lead
