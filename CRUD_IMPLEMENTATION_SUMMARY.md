# DataAir — Full CRUD Implementation Summary

This document summarizes the complete CRUD (Create, Read, Update, Delete, List) implementation for all systems in the DataAir platform.

---

## ✅ Complete CRUD Coverage

### 1. Knowledge Bases (`/api/v1/knowledge-bases/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` |
| List | GET | `/` |
| Get by ID | GET | `/{kb_id}` |
| Update | PUT | `/{kb_id}` |
| Delete | DELETE | `/{kb_id}` |
| Publish | POST | `/{kb_id}/publish` |
| Archive | POST | `/{kb_id}/archive` |
| Stats | GET | `/{kb_id}/stats` |

### 2. Documents (`/api/v1/documents/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create (inline) | POST | `/` |
| Upload file | POST | `/upload` |
| List | GET | `/` |
| Get by ID | GET | `/{doc_id}` |
| Get chunks | GET | `/{doc_id}/chunks` |
| Reindex | POST | `/{doc_id}/reindex` |
| Delete | DELETE | `/{doc_id}` |

### 3. Workflows (`/api/v1/workflows/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` |
| List | GET | `/` |
| Get by ID | GET | `/{wf_id}` |
| Update | PUT | `/{wf_id}` |
| Delete | DELETE | `/{wf_id}` |
| Execute | POST | `/{wf_id}/execute` |

### 4. Metadata Schemas (`/api/v1/metadata/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` |
| List | GET | `/` |
| Get by ID | GET | `/{schema_id}` |
| Update | PUT | `/{schema_id}` |
| Delete | DELETE | `/{schema_id}` |
| Validate | POST | `/{schema_id}/validate` |

### 5. Connectors / Sources (`/api/v1/connectors/sources`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/sources` |
| List | GET | `/sources` |
| Get by ID | GET | `/sources/{source_id}` |
| Update | PATCH | `/sources/{source_id}` |
| Delete | DELETE | `/sources/{source_id}` |
| Sync | POST | `/sources/{source_id}/sync` |
| Test (public) | POST | `/test` |
| Types (public) | GET | `/types` |

### 6. Work Groups (`/api/v1/work-groups/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` |
| List | GET | `/` |
| Get by ID | GET | `/{group_id}` |
| Update | PATCH | `/{group_id}` |
| Delete | DELETE | `/{group_id}` |
| List Members | GET | `/{group_id}/members` |
| Add Member | POST | `/{group_id}/members` |
| Remove Member | DELETE | `/{group_id}/members/{member_id}` |
| List Candidates | GET | `/{group_id}/candidates` |

### 7. Profiles (`/api/v1/profiles/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` |
| List | GET | `/` |
| Get by ID | GET | `/{profile_id}` |
| Update | PATCH | `/{profile_id}` |
| Delete | DELETE | `/{profile_id}` |
| Duplicate | POST | `/{profile_id}/duplicate` |
| Resolve | GET | `/{profile_id}/resolved` |
| **Services** | | |
| List Services | GET | `/{profile_id}/services` |
| Create Service | POST | `/{profile_id}/services` |
| Get Service | GET | `/{profile_id}/services/{service_id}` |
| Update Service | PATCH | `/{profile_id}/services/{service_id}` |
| Delete Service | DELETE | `/{profile_id}/services/{service_id}` |
| Reveal Secret | GET | `/{profile_id}/services/{service_id}/secret` (admin) |
| Health Check | POST | `/{profile_id}/services/{service_id}/health-check` |
| **Config Items** | | |
| List Config | GET | `/{profile_id}/config` |
| Create Config | POST | `/{profile_id}/config` |
| Update Config | PATCH | `/{profile_id}/config/{item_id}` |
| Delete Config | DELETE | `/{profile_id}/config/{item_id}` |

### 8. Tenants (`/api/v1/tenants/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` (admin) |
| List | GET | `/` |
| Get Current | GET | `/current` |
| Get by ID | GET | `/{tenant_id}` |
| Update | PUT | `/{tenant_id}` |
| Delete | DELETE | `/{tenant_id}` (admin) |

### 9. API Keys (`/api/v1/api-keys/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/` |
| List | GET | `/` |
| Usage List | GET | `/usage` |
| Usage Summary | GET | `/usage/summary` |
| Revoke | DELETE | `/{api_key_id}` |

### 10. Billing (`/api/v1/billing/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| List Plans | GET | `/plans` |
| Get Subscription | GET | `/subscription` |
| Update Subscription | PATCH | `/subscription` |
| Get Entitlements | GET | `/entitlements` |
| Create Checkout | POST | `/checkout` |
| Create Portal | POST | `/portal` |
| Stripe Webhook | POST | `/webhook` |
| Seed Plans | POST | `/seed-plans` |

### 11. Admin (`/api/v1/admin/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Platform Stats | GET | `/stats` |
| List Users | GET | `/users` |
| Update User | PATCH | `/users/{user_id}` |
| List Tenants | GET | `/tenants` |
| List Contact Messages | GET | `/contact-messages` |
| Update Contact Message | PATCH | `/contact-messages/{message_id}` |

### 12. Tags (`/api/v1/tags/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create | POST | `/tags` |
| List | GET | `/tags` |
| Get by ID | GET | `/tags/{tag_id}` |
| Update | PUT | `/tags/{tag_id}` |
| Delete | DELETE | `/tags/{tag_id}` |

### 13. Evaluation (`/api/v1/evaluation/`) — **NEWLY COMPLETED**
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Run Evaluation | POST | `/evaluate` |
| **Datasets** | | |
| Create Dataset | POST | `/datasets` |
| List Datasets | GET | `/datasets` |
| Get Dataset | GET | `/datasets/{dataset_id}` |
| Update Dataset | PUT | `/datasets/{dataset_id}` |
| Delete Dataset | DELETE | `/datasets/{dataset_id}` |
| **Runs** | | |
| List Runs | GET | `/runs` |
| Get Run | GET | `/runs/{run_id}` |

### 14. Governance (`/api/v1/governance/`) — **NEWLY COMPLETED**
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get Permissions | GET | `/permissions` |
| Get Roles | GET | `/roles` |
| **Policies** | | |
| Create Policy | POST | `/policies` |
| List Policies | GET | `/policies` |
| Get Policy | GET | `/policies/{policy_id}` |
| Update Policy | PUT | `/policies/{policy_id}` |
| Delete Policy | DELETE | `/policies/{policy_id}` |
| **Approvals** | | |
| Submit Approval | POST | `/approvals` |
| List Approvals | GET | `/approvals` |
| Get Approval | GET | `/approvals/{approval_id}` |
| Approve | POST | `/approvals/{approval_id}/approve` |
| Reject | POST | `/approvals/{approval_id}/reject` |
| **Audit** | | |
| Get Audit Logs | GET | `/audit` |

### 15. Search (`/api/v1/search/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Hybrid Search | POST | `/` |
| Keyword Search | POST | `/keyword` |
| Vector Search | POST | `/vector` |
| Graph Search | POST | `/graph` |

### 16. RAG (`/api/v1/rag/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| RAG Query | POST | `/` |

### 17. Chat (`/api/v1/chat/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| List Providers | GET | `/providers` |
| Create Completion | POST | `/` |
| Stream Completion | POST | `/stream` |

### 18. Contact (`/api/v1/contact/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Submit | POST | `/contact` |
| List Own | GET | `/contact/mine` |

### 19. Platform (`/api/v1/platform/`) — Read-only
| Operation | Method | Endpoint |
|-----------|--------|----------|
| Health | GET | `/platform/health` |
| Warehouse Sales | GET | `/warehouse/sales` |
| Warehouse Summary | GET | `/warehouse/sales/summary` |
| Warehouse Products | GET | `/warehouse/products/top` |
| Warehouse Categories | GET | `/warehouse/categories` |
| Warehouse ELT Runs | GET | `/warehouse/elt-runs` |
| Warehouse Quality | GET | `/warehouse/quality` |
| Warehouse Tables | GET | `/warehouse/tables` |
| List DAGs | GET | `/pipelines/dags` |
| Get DAG | GET | `/pipelines/dags/{dag_id}` |
| DAG Runs | GET | `/pipelines/dags/{dag_id}/runs` |
| DAG Tasks | GET | `/pipelines/dags/{dag_id}/runs/{run_id}/tasks` |
| Trigger DAG | POST | `/pipelines/dags/{dag_id}/trigger` |
| Pause DAG | PATCH | `/pipelines/dags/{dag_id}/pause` |
| Catalog Tables | GET | `/catalog/tables` |
| Catalog Search | GET | `/catalog/search` |
| Table Lineage | GET | `/catalog/lineage/{table_fqn}` |
| Glossary Terms | GET | `/catalog/glossary` |
| Storage Buckets | GET | `/storage/buckets` |
| Storage Objects | GET | `/storage/objects` |
| Storage Stats | GET | `/storage/stats` |
| Monitoring Query | GET | `/monitoring/query` |
| Monitoring Range | GET | `/monitoring/range` |
| Monitoring Summary | GET | `/monitoring/summary` |
| External Links | GET | `/links` |

### 20. System (`/api/v1/system/`)
| Operation | Method | Endpoint |
|-----------|--------|----------|
| System Status | GET | `/system/status` |

---

## 🔧 Models Added/Updated

### New Models
1. **`backend/app/models/governance.py`** — `GovernancePolicy`, `ApprovalWorkflow`
2. **Updated `backend/app/models/evaluation.py`** — Added `tenant_id` to both models, `kb_id` to `EvaluationRun`

### Relationships Added
- `Tenant` → `governance_policies`, `approval_workflows`
- `KnowledgeBase` → `approval_workflows`
- `Document` → `approval_workflows`
- `User` → `governance_policies`, `created_approvals`, `decided_approvals`

---

## 🧪 Test Results

```
Backend:  87 tests passed
Frontend: 21 tests passed
```

All existing tests pass without modification.

---

## 📝 Usage Examples

### Create Knowledge Base
```bash
curl -X POST http://localhost:8000/api/v1/knowledge-bases/ \
  -H "Cookie: dataair_access_token=..." \
  -H "X-CSRF-Token: ..." \
  -d '{"name": "My KB", "description": "Knowledge base for docs"}'
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Cookie: dataair_access_token=..." \
  -H "X-CSRF-Token: ..." \
  -F "kb_id=<kb_id>" \
  -F "file=@document.pdf"
```

### Create Evaluation Dataset
```bash
curl -X POST http://localhost:8000/api/v1/evaluation/datasets \
  -H "Cookie: dataair_access_token=..." \
  -H "X-CSRF-Token: ..." \
  -d '{"kb_id": "<kb_id>", "name": "Test Dataset", "questions": [{"q": "What is X?", "a": "Answer"}]}'
```

### Submit Approval
```bash
curl -X POST http://localhost:8000/api/v1/governance/approvals \
  -H "Cookie: dataair_access_token=..." \
  -H "X-CSRF-Token: ..." \
  -d '{"kb_id": "<kb_id>", "document_id": "<doc_id>", "creator_id": "<user_id>", "reviewers": ["<reviewer_id>"]}'
```

### Approve Document
```bash
curl -X POST http://localhost:8000/api/v1/governance/approvals/<approval_id>/approve \
  -H "Cookie: dataair_access_token=..." \
  -H "X-CSRF-Token: ..." \
  -d '{"reviewer_id": "<user_id>", "comments": "Looks good"}'
```

---

## 🚀 Next Steps

1. **Run migrations** to create new tables:
   ```bash
   make migrate
   ```

2. **Verify endpoints** work in Swagger UI at `http://localhost:8000/docs`

3. **Frontend integration** - Update frontend API client to use new endpoints

4. **Add pagination** to list endpoints that don't have it yet (most have it)

---

## 📄 License

Apache License 2.0