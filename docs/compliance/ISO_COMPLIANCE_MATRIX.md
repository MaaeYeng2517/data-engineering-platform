# ISO_COMPLIANCE_MATRIX.md

## 1. Objective
Matrix สำหรับวางแผนความพร้อม ISO/IEC 27001:2022 พร้อมการแมปไปยัง Control, หลักฐาน และสถานะการดำเนินงาน

> **หมายเหตุ:** นี่เป็น Preliminary Matrix ใช้สำหรับ Gap Analysis เท่านั้น ต้องตรวจสอบกับมาตรฐานฉบับเต็มและขอบเขตการรับรองที่องค์กรเลือก

## 2. ISO/IEC 27001:2022 Clauses 4–10

| Clause | Requirement | Implementation Plan | Evidence | Owner | Status | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| **4.1** | Understanding organization and needs | Context of organization analysis | Context Analysis, Interested Parties Register | ISMS Lead | To Do | P0 |
| **4.2** | Understanding needs/expectations | Stakeholder needs/requirements | Interested Parties Register (updated) | ISMS Lead | To Do | P0 |
| **4.3** | Determining scope of ISMS | Define scope, boundaries, exclusions with justification | ISMS Scope Statement (EV-001) | ISMS Lead | To Do | P0 |
| **4.4** | ISMS and its processes | Establish processes & interfaces | Process Map, Procedure List | ISMS Lead | To Do | P0 |
| **5.1** | Leadership & commitment | Management commitment, resources | Management Review Agenda/Minutes | Executive Sponsor | To Do | P0 |
| **5.2** | Policy | Approve Information Security Policy | Approved Security Policy (EV-001) | Executive Sponsor | To Do | P0 |
| **5.3** | Roles/responsibilities/authorities | Assign & communicate | Org Chart, Role Assignment Matrix | HR/Security | To Do | P0 |
| **6.1** | Actions to address risks/opportunities | Risk assessment & treatment | Risk Register, Risk Treatment Plan (EV-002) | Risk Owner | To Do | P0 |
| **6.2** | Information security objectives | Define measurable objectives | Security Objectives & KPI Plan | ISMS Lead | To Do | P0 |
| **6.3** | Planning of changes | Change control process | Change Management Procedure | Platform Lead | To Do | P0 |
| **7.1** | Resources | Allocate people/tech/infrastructure | Resource Plan | Executive Sponsor | To Do | P0 |
| **7.2** | Competence | Training & competence | Competency Matrix, Training Records | HR/Security | To Do | P0 |
| **7.3** | Awareness | Awareness program | Awareness Plan & Attendance | Security Lead | To Do | P0 |
| **7.4** | Communication | Internal/external comms | Communication Plan | ISMS Lead | To Do | P0 |
| **7.5** | Documented information | Document control | Document Register, Control Procedure | ISMS Lead | To Do | P0 |
| **8.1** | Operational planning & control | Implement controls & processes | Operational Procedures, Runbooks | Process Owners | To Do | P0 |
| **8.2** | Information security risk assessment | Perform at planned intervals | Risk Assessment Reports (EV-002) | Risk Owner | To Do | P0 |
| **8.3** | Information security risk treatment | Implement treatment plan | Risk Treatment Plan with Evidence | Risk Owner | To Do | P0 |
| **9.1** | Monitoring, measurement, analysis, evaluation | KPIs, metrics | KPI Dashboard/Reports | ISMS Lead | To Do | P0 |
| **9.2** | Internal audit | Audit programme & conduct | Internal Audit Plan/Report (EV-008) | Internal Auditor | To Do | P0 |
| **9.3** | Management review | Review inputs/outputs/actions | Management Review Minutes (EV-009) | Executive Sponsor | To Do | P0 |
| **10.1** | Nonconformity & corrective action | Handle NCs, RCA, follow-up | Nonconformity Register, CAPA (EV-010) | Process Owner | To Do | P0 |
| **10.2** | Continual improvement | Improve ISMS effectiveness | Improvement Actions Log | ISMS Lead | To Do | P0 |

## 3. ISO/IEC 27001:2022 Annex A Mapping (Key Controls)

| Control ID | Control Name | Applicability (Y/N/TBD) | Implementation | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| **A.5.1** | Policies for information security | TBD | Approved Security Policy | Policy Doc (signed) | Security Lead | To Do |
| **A.5.2** | Information security roles/responsibilities | TBD | RACI/Role Matrix | Role Assignment | Security Lead | To Do |
| **A.5.15** | Access control | TBD | RBAC + Least Privilege + SoD | RBAC Matrix, Access Reviews | IAM Lead | To Do |
| **A.5.16** | Identity management | TBD | IdP + Unique IDs | IdP Config, User Registry | IAM Lead | To Do |
| **A.5.17** | Authentication information | TBD | MFA, Password Policy, Secrets Mgmt | MFA Policy/Logs | IAM Lead | To Do |
| **A.5.24** | Information security incident management | TBD | Incident Response Plan/Playbooks | Incident Register (EV-005) | Security Lead | To Do |
| **A.5.28** | Collection of evidence | TBD | Evidence Register + Chain of Custody | Evidence Records | Security Lead | To Do |
| **A.6.2** | Terms/conditions of employment | TBD | Security Clauses | HR Templates | HR Lead | To Do |
| **A.6.3** | Awareness, education, training | TBD | Training Program | Training Records | Security Lead | To Do |
| **A.7.1-A.7.4** | Physical security | TBD | Access Control, Asset Protection | Physical Logs/Inventory | Facility/Security | To Do |
| **A.8.1-A.8.3** | User endpoint/asset management | TBD | Asset Inventory, Acceptable Use | Asset Register | IT/Security | To Do |
| **A.8.9** | Configuration management | TBD | Baseline Config, Hardening | Config Baselines | Platform Lead | To Do |
| **A.8.10** | Information deletion | TBD | Secure Deletion/Retention | Disposal Records | Data Owner/Security | To Do |
| **A.8.11** | Data masking | TBD | Masking/Tokenization | Masking Policy/Tests | Data Steward | To Do |
| **A.8.12** | Data leakage prevention | TBD | DLP considerations/Controls | Policy/Controls | Security Lead | To Do |
| **A.8.13** | Information backup | TBD | Backup Policy + Testing | Backup Plan, Restore Tests (EV-006) | Infra Lead | To Do |
| **A.8.14** | Redundancy | TBD | HA/Resilience | DR Plan/Tests | Infra Lead | To Do |
| **A.8.15** | Logging | TBD | Centralized Logging, Correlation ID | Log Config/Audit Logs | Security/Platform | To Do |
| **A.8.16** | Monitoring activities | TBD | SIEM/Alerts | Monitoring Rules/Alerts | Security Lead | To Do |
| **A.8.23** | Web filtering | TBD | Egress Control | Policy/Rules | Network Lead | To Do |
| **A.8.24** | Use of cryptography | TBD | Crypto Policy, Key Management | Crypto Policy/KMS Logs | Security Lead | To Do |
| **A.8.25** | Secure development life cycle | TBD | Secure SDLC, Code Review | SDLC Policy, Reviews | Eng Lead | To Do |
| **A.8.26** | Application security requirements | TBD | Security Requirements | Requirements Checklist | Eng Lead | To Do |
| **A.8.27** | Secure system architecture & engineering | TBD | Secure Architecture Review | Architecture Review | Solution Architect | To Do |
| **A.8.28** | Secure coding | TBD | Secure Coding Guidelines | Guidelines/Training | Eng Lead | To Do |
| **A.8.29** | Security testing in development & acceptance | TBD | SAST/DAST/Dependency Scan | Scan Reports | Security/QA | To Do |
| **A.8.31** | Separation of environments | TBD | Dev/Staging/Prod Separation | Network/Env Diagram | Platform Lead | To Do |
| **A.8.32** | Change management | TBD | Change Control Workflow | Change Tickets (EV-007) | Platform Lead | To Do |

## 4. Evidence Register Mapping
| Evidence ID | Reference | Required For | Review Cycle |
| --- | --- | --- | --- |
| EV-001 | ISMS Scope, Policy, Org Structure | Clauses 4–5, A.5.1-A.5.2 | Annual / On Change |
| EV-002 | Risk Register & Treatment Plan | Clauses 6,8 | Quarterly / On Change |
| EV-003 | Statement of Applicability | Clauses 6.1.3 | Quarterly / On Change |
| EV-004 | User Access Review | A.5.15-A.5.16 | Quarterly |
| EV-005 | Incident Records | A.5.24, A.5.28 | Per Incident + Quarterly |
| EV-006 | Backup & Restore Test | A.8.13-A.8.14 | Semi-Annual / After Major Change |
| EV-007 | Change Management | A.8.32 | Monthly Review |
| EV-008 | Internal Audit Report | Clause 9.2 | Annual / Per Audit Plan |
| EV-009 | Management Review Minutes | Clause 9.3 | At least Annually |
| EV-010 | Corrective Action Register | Clause 10 | Ongoing / Monthly Review |

## 5. Gap Analysis Template
| Area | Current State | Target State (ISO/IEC 27001) | Gap | Action Plan | Owner | Due Date | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Scope** | TBD | Defined & Approved | TBD | Define ISMS Scope | ISMS Lead | TBD | P0 |
| **Risk** | TBD | Risk Assessment Done | TBD | Conduct Risk Assessment | Risk Owner | TBD | P0 |
| **SoA** | TBD | Completed & Approved | TBD | Draft SoA | ISMS Lead | TBD | P0 |
| **Access Control** | TBD | Enforced with Reviews | TBD | Implement RBAC + Reviews | IAM Lead | TBD | P0 |
| **Audit/Logging** | TBD | Centralized & Protected | TBD | Enable Immutable Audit | Security Lead | TBD | P0 |
| **Backup/DR** | TBD | Tested Restore | TBD | DR Plan + Tests | Infra Lead | TBD | P0 |
| **Incidents** | TBD | Process in Place | TBD | Incident Response | Security Lead | TBD | P0 |
| **Internal Audit** | TBD | Performed Independently | TBD | Audit Plan & Execution | Internal Auditor | TBD | P0 |

## 6. Readiness Checklist
- [ ] ISMS Scope approved
- [ ] Information Security Policy approved
- [ ] Risk Register & Treatment Plan complete
- [ ] Statement of Applicability approved
- [ ] Roles/Responsibilities assigned
- [ ] Access Control implemented & reviewed
- [ ] Logging/Audit enabled
- [ ] Backup & Restore tested with evidence
- [ ] Incident Management in place
- [ ] Training/Awareness completed
- [ ] Internal Audit conducted
- [ ] Management Review held
- [ ] Corrective Actions tracked to closure
- [ ] Evidence Register up to date

**เวอร์ชัน:** 1.0 | **สถานะ:** Draft for Gap Analysis | **ผู้รับผิดชอบ:** ISMS Lead
