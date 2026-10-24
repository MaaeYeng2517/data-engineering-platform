# DATA_GOVERNANCE_POLICY.md

## 1. Purpose
กำหนดหลักการ, บทบาท, ความรับผิดชอบ, กฎระเบียบ และกระบวนการกำกับดูแลข้อมูลขององค์กร เพื่อให้การใช้ข้อมูลถูกต้อง ปลอดภัย และตรวจสอบได้ ตามหลัก Governance by Design

## 2. Scope
ครอบคลุมข้อมูลทุกประเภทที่จัดเก็บ/ประมวลผลใน Enterprise Data Platform รวมถึง Metadata, Data Products, Lineage, Audit Logs และหลักฐานที่เกี่ยวข้อง

## 3. Governance Principles
| หลักการ | คำอธิบาย |
| --- | --- |
| **Accountability** | มี Data Owner ที่รับผิดชอบชัดเจนสำหรับแต่ละชุดข้อมูล |
| **Transparency** | Metadata, Lineage, Classification ต้องเปิดเผยภายในขอบเขตที่ได้รับอนุญาต |
| **Integrity** | ข้อมูลต้องถูกต้อง ครบถ้วน และมีที่มาที่เชื่อถือได้ |
| **Security & Privacy** | คุ้มครองข้อมูลตามชั้นความลับและกฎหมายที่เกี่ยวข้อง |
| **Compliance** | ปฏิบัติตามนโยบายภายในและข้อกำหนดมาตรฐานที่องค์กรเลือก |
| **Lifecycle Management** | จัดการข้อมูลตั้งแต่การสร้างจนถึงการทำลายตามนโยบาย |

## 4. Governance Structure
| Role | Authority | Responsibility |
| --- | --- | --- |
| **Data Governance Committee (DGC)** | อนุมัตินโยบาย, มาตรฐาน, ข้อยกเว้น | กำกับดูแลภาพรวม, ทบทวนประจำเดือน/ไตรมาส |
| **Data Governance Lead** | ประสานงาน Governance ทั่วองค์กร | ดูแลการบังคับใช้นโยบาย, Evidence Register, Readiness |
| **Data Owner** | อนุมัติการใช้/เผยแพร่ในโดเมน | รับผิดชอบความหมาย, คุณภาพ, ความเสี่ยงของชุดข้อมูล |
| **Data Steward** | ดำเนินการในเชิงปฏิบัติ | จัดการ Metadata, Glossary, Quality Rules, ช่วย Data Owner |
| **Security & Privacy Lead** | ควบคุมความเสี่ยงด้านความปลอดภัย/ความเป็นส่วนตัว | ประเมินผลกระทบ, ตรวจสอบสิทธิ์, Incident Response |
| **Platform Lead** | ดูแลระบบและ Enforcement | บังคับใช้ Policy, Logging, Access Control |

## 5. Data Classification
| ระดับ | คำจำกัดความ | ตัวอย่าง | การควบคุมขั้นต่ำ |
| --- | --- | --- | --- |
| **Public** | สามารถเปิดเผยต่อสาธารณะได้เมื่อได้รับอนุมัติ | ข้อมูลที่เผยแพร่สาธารณะ | Review ก่อนเผยแพร่ |
| **Internal** | ใช้ภายในองค์กรเท่านั้น | คู่มือภายใน, รายงานทั่วไป | เข้าถึงผ่านบัญชีองค์กร, ไม่ส่งต่อภายนอกโดยไม่อนุมัติ |
| **Confidential** | ข้อมูลธุรกิจที่มีมูลค่าหรือจำกัดการเผยแพร่ | สัญญา, ราคา, แผนธุรกิจ | Least Privilege, Audit, ห้ามดาวน์โหลดโดยไม่จำเป็น |
| **Restricted** | มีความอ่อนไหวสูง สูงสุด | ข้อมูลส่วนบุคคลสำคัญ, ข้อมูลการเงินละเอียดอ่อน, Credentials | Least Privilege + MFA, Column Masking/Row Filter, Strict Audit, Need-to-Know |

## 6. Data Ownership & Stewardship
- **Data Owner** ต้องได้รับการแต่งตั้งเป็นลายลักษณ์อักษรและบันทึกใน `data_domains`
- **Data Steward** รองรับ Data Owner ในการดูแล Metadata และคุณภาพ
- **ทุก Dataset** ต้องมี `owner_user_id` ที่ใช้งานได้
- **เมื่อย้ายตำแหน่ง/ลาออก** ต้องโอนกรรมสิทธิ์ข้อมูลภายในเวลาที่กำหนด

## 7. Data Product Lifecycle
| สถานะ | คำอธิบาย | การควบคุม |
| --- | --- | --- |
| **draft** | กำลังพัฒนา ยังไม่เผยแพร่ | เฉพาะเจ้าของ+ผู้ได้รับอนุญาต |
| **pending_approval** | รอการอนุมัติจาก Data Owner/Committee | Workflow ต้องบังคับ, Audit บันทึก |
| **published** | ได้รับอนุมัติ เป็น Certified Data Product | เข้าถึงตามสิทธิ์, มี Lineage/Quality ครบ |
| **deprecated** | เลิกใช้แล้ว แนะนำให้ใช้รุ่นใหม่ | แจ้งผู้ใช้งาน, จำกัดการใช้งานใหม่ |
| **archived** | ไม่ใช้งานแล้ว เก็บตาม Retention | อ่านอย่างจำกัด, ไม่รวมใน Search หลัก |

## 8. Data Quality
- **Quality Rules** ต้องกำหนดต่อ Dataset สำคัญ
- **Critical Rules** – หากไม่ผ่านต้องมีการ Quarantine หรือ Block Publishing
- **Quality Results** บันทึกทุกครั้งที่รัน Pipeline
- **Data Contracts** ควรพิจารณาสำหรับ Data Product ที่ใช้ร่วมกัน
- **Remediation** – มีแผนแก้ไขและติดตามจนปิด

## 9. Data Lineage
- บันทึกความสัมพันธ์ `source -> transformation -> target`
- ต้องระบุ `pipeline_id`, `dataset_version_id`
- ใช้สำหรับ Impact Analysis, Root Cause Analysis, Compliance Review
- ครอบคลุมอย่างน้อย Dataset สำคัญ

## 10. Retention, Archival & Disposal
| ประเภทข้อมูล | Retention (แนวทาง) | การจัดการ |
| --- | --- | --- |
| **Operational Metadata** | ตามความจำเป็นทางธุรกิจ + กฎหมาย | Archive หลังหมดอายุ |
| **Audit Logs** | ตามข้อกำหนดความปลอดภัย/กฎหมาย (ไม่น้อยกว่าที่กำหนด) | Immutable, แยก Storage, จำกัดการลบ |
| **Business Data** | กำหนดโดย Data Owner + Legal/Security | Archive/Disposal ตามนโยบาย |
| **Backups** | ตาม DR Policy | Rotate, Encrypt, ทดสอบ Restore |
| **Evidence** | ตามรอบการตรวจประเมิน/กฎหมาย | คงไว้จนกว่าการตรวจประเมินปิด |

**การทำลายข้อมูล:** ต้องมีการอนุมัติ, บันทึกใน Audit, ตรวจสอบว่าไม่มี Derived Data ที่ยังต้องเก็บ

## 11. Access Request & Approval
1. ผู้ขอส่งคำขอผ่าน `Approvals` API พร้อมเหตุผล/ระยะเวลา
2. Data Owner/ผู้มีอำนาจพิจารณา
3. ถ้าเป็นข้อมูล Restricted ต้องมีการพิจารณาเพิ่มเติม
4. การอนุมัติ/ปฏิเสธบันทึกใน Audit
5. สิทธิ์มีอายุและต้องทบทวน

## 12. Policy Enforcement
- **Preventive** – RBAC, Network Policy, Encryption
- **Detective** – Logging, Monitoring, Alerts
- **Corrective** – Incident Response, Access Revocation, CAPA

## 13. Exceptions
การขอข้อยกเว้นต้องยื่นเป็นลายลักษณ์อักษรผ่าน Data Governance Committee โดยระบุ: เหตุผล, ความเสี่ยง, มาตรการชดเชย, ระยะเวลา, ผู้รับผิดชอบ, การทบทวน

ทุกข้อยกเว้นต้องบันทึกใน Risk Register และทบทวนก่อนหมดอายุ

## 14. Training & Awareness
- **Onboarding** – หลักสูตร Data Governance & Security
- **Annual/Refresher** – ทบทวนเป็นประจำ
- **Role-based** – เน้นตามบทบาท (Data Owner/Steward/Engineer)
- **Records** – บันทึกการอบรมใน Evidence Register

## 15. Review
นโยบายนี้ทบทวนอย่างน้อย **ปีละ 1 ครั้ง** หรือเมื่อมีการเปลี่ยนแปลงที่มีนัยสำคัญ (กฎหมาย/เทคโนโลยี/องค์กร) โดย Data Governance Committee อนุมัติ

**อนุมัติโดย:** Data Governance Committee  
**ผู้รับผิดชอบ:** Data Governance Lead  
**เวอร์ชัน:** 1.0 | **วันที่มีผล:** 2025-10-24 | **สถานะ:** Approved for Implementation
