# DataAir Implementation Roadmap

## Project Overview

Building **DataAir** - Enterprise Data Operating & Intelligence Platform from the existing codebase.

## Current State Analysis

### Existing Components (from codebase audit)

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI Backend | Partial | Main app, auth, basic models exist |
| PostgreSQL Models | Partial | Users, Tenants, Knowledge bases, Documents, Chunks, Entities |
| Authentication | Partial | JWT, Register, Login, Refresh, CSRF |
| Connectors | Mock | BaseConnector + 6 mock implementations |
| Ingestion | Mock | IngestionEngine with mock processors |
| Processing | Mock | TextProcessor, Chunker, EntityExtractor |
| Indexing | Mock | KeywordIndex, VectorIndex (in-memory) |
| Retrieval | Mock | Hybrid search, reranking |
| RAG | Mock | ContextBuilder, placeholder LLM |
| Knowledge Graph | Mock | NetworkX in-memory |
| Workers | Mock | In-memory task queue |
| Frontend | Missing | Only empty directories exist |
| Docker | Missing | Only init.sql exists |
| Tests | Partial | Integration test script exists |

### Technology Gaps

1. **No Docker/Docker Compose** - Need full container orchestration
2. **No Frontend** - Next.js app needs to be created
3. **No Alembic Migrations** - Using raw SQL init.sql
4. **Mock Services** - All data services are in-memory mocks
5. **No Real Connectors** - PostgreSQL, MySQL, CSV, Excel, REST API, MinIO missing
6. **No Vector DB Integration** - pgvector/Qdrant not connected
7. **No Real LLM Integration** - OpenAI/Anthropic/Ollama not implemented
8. **No Monitoring** - OpenTelemetry, Prometheus, Grafana missing
9. **No CI/CD** - GitHub Actions needed
10. **No Security Hardening** - Rate limiting, input validation, etc.

## Phase Breakdown

### Phase 0: Project Audit & Planning ✓ (Current)
- [x] Audit existing codebase
- [x] Create architecture.md
- [x] Create roadmap.md (this document)
- [ ] Create development.md

### Phase 1: Foundation (Week 1)
- [ ] Docker Compose with all services
- [ ] Dockerfile for backend
- [ ] Dockerfile for frontend
- [ ] .env.example with all config
- [ ] Next.js 14+ frontend setup
- [ ] Health check endpoints
- [ ] Verify all services start

### Phase 2: Database Foundation (Week 1-2)
- [ ] Alembic migration setup
- [ ] Complete schema with all entities
- [ ] UUID, timestamps, indexes, FKs, constraints
- [ ] Migration from clean database
- [ ] Seed data scripts

### Phase 3: Authentication & IAM (Week 2)
- [ ] Complete auth flow (register, login, logout, refresh)
- [ ] Password hashing (bcrypt)
- [ ] JWT with proper claims
- [ ] Role-based access control
- [ ] Permission system
- [ ] Organization/Workspace/Team models
- [ ] Tenant isolation enforcement
- [ ] Cross-tenant access prevention tests

### Phase 4: Data Source Management (Week 2-3)
- [ ] Connector abstraction interface
- [ ] PostgreSQL connector (real)
- [ ] MySQL connector (real)
- [ ] CSV connector (real)
- [ ] JSON connector (real)
- [ ] Excel connector (real)
- [ ] REST API connector (real)
- [ ] MinIO/S3 connector (real)
- [ ] Connection testing
- [ ] Schema discovery
- [ ] Credential management (encrypted)

### Phase 5: Data Ingestion (Week 3)
- [ ] Batch ingestion jobs
- [ ] File ingestion (upload + process)
- [ ] Database ingestion (CDC/snapshot)
- [ ] API ingestion (pagination, auth)
- [ ] Scheduled ingestion (cron)
- [ ] Ingestion job tracking (status, records, errors, logs)
- [ ] Incremental sync support

### Phase 6: Raw Data Storage (Week 3-4)
- [ ] Immutable raw storage structure
- [ ] Path: /raw/{org}/{source}/{dataset}/{year}/{month}/{day}/
- [ ] Checksum validation
- [ ] Versioning
- [ ] Metadata tracking
- [ ] MinIO integration
- [ ] Tenant isolation

### Phase 7: Dataset Management (Week 4)
- [ ] Datasets CRUD
- [ ] Dataset versions
- [ ] Dataset columns/schema
- [ ] Tags, owners, descriptions
- [ ] UI: Dataset list, detail, schema, preview, versions

### Phase 8: Data Processing (Week 4-5)
- [ ] Transform operations: Select, Filter, Rename, Cast, Remove Duplicate, Fill Missing, Join, Aggregate, Sort, Calculate Column
- [ ] SQL Transform
- [ ] Python Transform
- [ ] Pipeline: Extract → Validate → Clean → Transform → Load
- [ ] Real processing with Pandas/Polars/DuckDB

### Phase 9: Data Quality (Week 5)
- [ ] Quality rules: Not Null, Unique, Type, Range, Regex, Duplicate, Completeness, Consistency, Freshness, Referential Integrity
- [ ] Quality scores: Overall, Completeness, Validity, Uniqueness, Consistency, Freshness
- [ ] Quality engine with rule evaluation
- [ ] Test with valid/invalid datasets

### Phase 10: Bronze/Silver/Gold Layers (Week 5-6)
- [ ] Logical layer implementation
- [ ] Pipeline: Raw → Bronze → Silver → Gold
- [ ] Layer-specific processing
- [ ] Metadata propagation
- [ ] Test with real data

### Phase 11: Metadata Catalog (Week 6)
- [ ] Dataset metadata
- [ ] Column metadata
- [ ] Owners, tags, descriptions
- [ ] Classification
- [ ] Quality scores in catalog
- [ ] Usage tracking
- [ ] Global search API + UI

### Phase 12: Data Lineage (Week 6-7)
- [ ] Dataset lineage
- [ ] Column lineage
- [ ] Pipeline lineage
- [ ] Workflow lineage
- [ ] Visual lineage graph (React Flow)
- [ ] Automatic lineage capture

### Phase 13: Data Governance (Week 7)
- [ ] Classification (PII, sensitive, public)
- [ ] Policies (access, retention, sharing)
- [ ] Owners, stewards
- [ ] Permissions
- [ ] AI usage policy
- [ ] Export policy
- [ ] Enforcement tests

### Phase 14: Audit Log (Week 7)
- [ ] Centralized audit logging
- [ ] Track: Login, CRUD operations, workflow execution, data export, permission changes, policy changes
- [ ] Immutable storage
- [ ] Query API

### Phase 15: Data Studio (Week 7-8)
- [ ] React Flow integration
- [ ] Nodes: Source, Read, Filter, Clean, Transform, Join, Aggregate, Quality, Store, API, Export
- [ ] Drag, drop, connect, configure
- [ ] Save, validate, run, delete
- [ ] Real backend execution (not UI-only)

### Phase 16: Workflow Engine (Week 8)
- [ ] Workflow definition (nodes, edges)
- [ ] Workflow runs & tasks
- [ ] Worker implementation
- [ ] Retry logic
- [ ] Logs
- [ ] Statuses: Pending, Running, Success, Failed, Cancelled, Retrying

### Phase 17: Scheduler (Week 8-9)
- [ ] Manual run
- [ ] Scheduled run (cron)
- [ ] Recurring: 5min, hourly, daily, weekly
- [ ] Timezone support
- [ ] Automatic execution verification

### Phase 18: Data API (Week 9)
- [ ] Dataset API
- [ ] Metadata API
- [ ] Query API
- [ ] Workflow API
- [ ] Quality API
- [ ] Lineage API
- [ ] Pagination, filtering, sorting
- [ ] Auth + Authorization on all endpoints

### Phase 19: Data Explorer & Analytics (Week 9-10)
- [ ] Data Explorer UI
- [ ] SQL Query interface
- [ ] Table preview
- [ ] Charts (Recharts)
- [ ] Dashboard builder
- [ ] Permissions on queries

### Phase 20: Knowledge Base (Week 10)
- [ ] Knowledge Base CRUD
- [ ] Document upload
- [ ] Parsing (PDF, TXT, Markdown, CSV, JSON)
- [ ] Chunking
- [ ] Metadata extraction
- [ ] Embedding generation

### Phase 21: Vector Search (Week 10-11)
- [ ] Vector storage abstraction
- [ ] pgvector integration
- [ ] Qdrant integration
- [ ] Pipeline: Document → Chunk → Embedding → Vector Store
- [ ] Semantic search

### Phase 22: RAG (Week 11)
- [ ] Question → Query Processing → Retrieval → Reranking → Context → LLM → Answer
- [ ] LLM abstraction (provider-agnostic)
- [ ] Real LLM integration (OpenAI, Anthropic, Ollama)
- [ ] Context citation
- [ ] Test with real KB

### Phase 23: AI Model Gateway (Week 11-12)
- [ ] Model Provider abstraction
- [ ] Model configuration
- [ ] API Key management
- [ ] Usage tracking
- [ ] Token counting
- [ ] Cost estimation
- [ ] Providers: OpenAI, Anthropic, Gemini, Ollama, vLLM

### Phase 24: AI Agent Foundation (Week 12)
- [ ] Agent architecture
- [ ] Goal, Planning, Tools, Execution, Memory, Verification
- [ ] DataOS permissions integration
- [ ] IAM enforcement for agents

### Phase 25: MCP / Tool System (Week 12)
- [ ] Tool abstraction
- [ ] Tools: Search Dataset, Query Dataset, Run Workflow, Inspect Metadata, Search Knowledge, Run Data Quality
- [ ] MCP compatibility
- [ ] Audit logging for tool calls

### Phase 26: Monitoring & Observability (Week 12-13)
- [ ] Structured logging
- [ ] Metrics (Prometheus)
- [ ] Traces (OpenTelemetry)
- [ ] Health checks
- [ ] Alerts
- [ ] Grafana dashboards
- [ ] Monitor: CPU, Memory, Storage, API latency, Error rate, Jobs, Workflows, Quality, AI Usage

### Phase 27: Security Hardening (Week 13)
- [ ] Security review
- [ ] Auth/Authorization testing
- [ ] Tenant isolation testing
- [ ] SQL Injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] CORS configuration
- [ ] Rate limiting
- [ ] Secrets management
- [ ] File upload security
- [ ] API security
- [ ] Audit logging verification

### Phase 28: Performance Testing (Week 13-14)
- [ ] API load testing
- [ ] Database performance
- [ ] Ingestion throughput
- [ ] Processing performance
- [ ] Workflow execution
- [ ] Search performance
- [ ] Vector search performance
- [ ] Bottleneck identification
- [ ] Optimization

### Phase 29: End-to-End Test (Week 14)
- [ ] Complete workflow: User → Org → Source → Ingest → Store → Dataset → Process → Quality → Metadata → Lineage → Workflow → KB → Vector → RAG → AI → Audit → Monitor
- [ ] All real implementations
- [ ] No mocks for final E2E

### Phase 30: Regression Test (Week 14)
- [ ] Run ALL previous phase tests
- [ ] 0 critical failures
- [ ] 0 blocking failures
- [ ] All core tests PASS

### Phase 31: Production Build (Week 14-15)
- [ ] Frontend production build
- [ ] Backend production config
- [ ] Database migrations
- [ ] Docker images
- [ ] Environment variables
- [ ] Secrets management
- [ ] Health checks
- [ ] Logging config

### Phase 32: Final Acceptance Test (Week 15)
- [ ] Authentication tests
- [ ] Data tests
- [ ] Management tests
- [ ] Studio tests
- [ ] Knowledge tests
- [ ] AI tests
- [ ] Operations tests

### Phase 33: Final Usability Test (Week 15)
- [ ] Clean environment start
- [ ] Complete business workflow via UI
- [ ] No manual DB modifications

### Phase 34: Final Clean Build (Week 15)
- [ ] docker compose down -v
- [ ] docker compose build --no-cache
- [ ] docker compose up -d
- [ ] Run migrations
- [ ] Run all tests
- [ ] Verify all services

### Phase 35: Final Acceptance Criteria (Week 15)
- [ ] All 32 component checks PASS

### Phase 36: Final Report (Week 15)
- [ ] docs/final-report.md
- [ ] TEST-REPORT.md

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Scope creep | Strict phase gates, no skipping |
| Mock services becoming permanent | Replace mocks immediately in each phase |
| Database migration issues | Test migrations from clean DB each phase |
| Frontend/backend integration | Contract-first API design |
| Performance at scale | Early profiling in Phase 28 |
| Security vulnerabilities | Phase 27 dedicated security review |

## Success Criteria

**Phase 0 PASS**: Documentation complete, roadmap approved
**Phase 1 PASS**: All containers running, health checks pass
**Phase 2 PASS**: Migrations run clean, all models queryable
**Phase 3 PASS**: Auth flow works, tenant isolation verified
**Phase 4 PASS**: All 7 connectors work with real connections
**Phase 5 PASS**: Real ingestion stores data in raw storage
**Phase 6 PASS**: Raw storage verified with checksums
**Phase 7 PASS**: Dataset CRUD + UI functional
**Phase 8 PASS**: Real transforms produce correct output
**Phase 9 PASS**: Quality engine detects injected errors
**Phase 10 PASS**: Data flows through all 3 layers correctly
**Phase 11 PASS**: Search returns relevant results
**Phase 12 PASS**: Lineage graph auto-generated and accurate
**Phase 13 PASS**: Governance policies enforced
**Phase 14 PASS**: Audit events recorded for all actions
**Phase 15 PASS**: Visual workflow executes on backend
**Phase 16 PASS**: Workflow engine handles all statuses
**Phase 17 PASS**: Scheduled workflows execute automatically
**Phase 18 PASS**: All APIs functional with auth
**Phase 19 PASS**: Explorer queries real data
**Phase 20 PASS**: KB ingests and processes documents
**Phase 21 PASS**: Semantic search returns relevant results
**Phase 22 PASS**: RAG answers questions from KB
**Phase 23 PASS**: Model gateway routes to real providers
**Phase 24 PASS**: Agent executes permitted tasks
**Phase 25 PASS**: Agent calls tools, results return, audit logs
**Phase 26 PASS**: Metrics, logs, traces visible in Grafana
**Phase 27 PASS**: No critical/high vulnerabilities
**Phase 28 PASS**: Performance meets SLAs
**Phase 29 PASS**: Complete E2E workflow succeeds
**Phase 30 PASS**: Zero regressions
**Phase 31 PASS**: Production build deploys successfully
**Phase 32 PASS**: All acceptance criteria met
**Phase 33 PASS**: Usable end-to-end via UI
**Phase 34 PASS**: Clean rebuild passes all tests
**Phase 35 PASS**: All 32 checks PASS
**Phase 36 PASS**: Reports generated

## Timeline Estimate

- **Phase 0-3**: 2 weeks (Foundation + Auth)
- **Phase 4-10**: 4 weeks (Data Pipeline core)
- **Phase 11-14**: 2 weeks (Metadata, Lineage, Governance, Audit)
- **Phase 15-19**: 3 weeks (Studio, Workflow, Scheduler, API, Analytics)
- **Phase 20-25**: 3 weeks (Knowledge, Vector, RAG, AI, Agents)
- **Phase 26-30**: 2 weeks (Monitoring, Security, Performance, E2E, Regression)
- **Phase 31-36**: 2 weeks (Production, Final Tests, Reports)

**Total: ~18 weeks** (4.5 months) for full implementation with one engineer.

With parallel workstreams: ~10-12 weeks.

## Dependencies

```
Phase 1 → Phase 2 → Phase 3
Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 10
Phase 7 → Phase 11 → Phase 12
Phase 10 → Phase 13
Phase 3 → Phase 14
Phase 7,8,16 → Phase 15
Phase 15 → Phase 16 → Phase 17
Phase 7,10,11,12,13,14,16 → Phase 18
Phase 7,10,18 → Phase 19
Phase 3,5,6,8,20,21 → Phase 22
Phase 22 → Phase 23 → Phase 24 → Phase 25
All → Phase 26
All → Phase 27
All → Phase 28
All → Phase 29
All → Phase 30
Phase 31 → Phase 32 → Phase 33 → Phase 34 → Phase 35 → Phase 36
```

## Team Allocation (if multiple engineers)

| Engineer | Focus Areas |
|----------|-------------|
| Backend 1 | Phases 1-3, 16-18, 26-27 |
| Backend 2 | Phases 4-10, 14-15 |
| Backend 3 | Phases 11-13, 20-25 |
| Frontend | Phases 1, 7, 11, 15, 19, 33 |
| DevOps | Phases 1, 26, 31, 34 |
| QA | Phases 3, 5, 9, 12, 14, 17, 21, 22, 25, 28-35 |

---

*Roadmap created: 2026-09-25*
*Version: 1.0*