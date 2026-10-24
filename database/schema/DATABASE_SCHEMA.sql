-- DATABASE_SCHEMA.sql
-- Enterprise Data Platform - Control Database Schema (PostgreSQL)
-- Version: 1.0 | Status: Draft for Review
-- Note: For Metadata/Control Plane only. Business data should reside in Object Storage/Lakehouse

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- ORGANIZATIONS
-- =============================================
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================
-- USERS
-- =============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    identity_subject VARCHAR(255) NOT NULL,
    email VARCHAR(320) NOT NULL,
    full_name VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','suspended')),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_org_subject UNIQUE (organization_id, identity_subject),
    CONSTRAINT uq_users_org_email UNIQUE (organization_id, email)
);

-- =============================================
-- ROLES & PERMISSIONS
-- =============================================
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    scope_type VARCHAR(30) NOT NULL CHECK (scope_type IN ('organization','domain','dataset')),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_roles_org_name UNIQUE (organization_id, name)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    CONSTRAINT uq_permissions_resource_action UNIQUE (resource, action)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    scope_id UUID,
    scope_type VARCHAR(30),
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    reason TEXT,
    PRIMARY KEY (user_id, role_id, COALESCE(scope_id, '00000000-0000-0000-0000-000000000000'::uuid))
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- =============================================
-- DATA GOVERNANCE
-- =============================================
CREATE TABLE data_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_data_domains_org_name UNIQUE (organization_id, name)
);

CREATE TABLE retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    retention_days INTEGER NOT NULL CHECK (retention_days >= 0),
    archive_after_days INTEGER,
    delete_after_days INTEGER,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_retention_policies_org_name UNIQUE (organization_id, name)
);

CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    connection_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    credential_ref VARCHAR(255),
    owner_user_id UUID REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','error')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_data_sources_org_name UNIQUE (organization_id, name)
);

-- =============================================
-- DATASETS & VERSIONS
-- =============================================
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    domain_id UUID NOT NULL REFERENCES data_domains(id) ON DELETE RESTRICT,
    owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    source_id UUID REFERENCES data_sources(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    classification VARCHAR(20) NOT NULL CHECK (classification IN ('public','internal','confidential','restricted')),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','pending_approval','published','deprecated','archived')),
    retention_policy_id UUID REFERENCES retention_policies(id),
    purpose TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_reviewed_at TIMESTAMPTZ,
    CONSTRAINT uq_datasets_org_domain_name UNIQUE (organization_id, domain_id, name)
);

CREATE TABLE dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL CHECK (version_number > 0),
    schema_hash VARCHAR(128) NOT NULL,
    schema_definition JSONB NOT NULL,
    location_ref VARCHAR(1024),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dataset_versions UNIQUE (dataset_id, version_number)
);

-- =============================================
-- PIPELINES & RUNS
-- =============================================
CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    schedule_cron VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','active','paused','disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_pipelines_org_name UNIQUE (organization_id, name)
);

CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('manual','scheduled','event')),
    triggered_by UUID REFERENCES users(id),
    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_ms INTEGER,
    error_code VARCHAR(100),
    error_message TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================
-- DATA QUALITY
-- =============================================
CREATE TABLE quality_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    definition JSONB NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'high' CHECK (severity IN ('low','medium','high','critical')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE quality_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES quality_rules(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('passed','failed','skipped')),
    passed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    details JSONB DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================
-- LINEAGE
-- =============================================
CREATE TABLE data_lineage_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    source_dataset_id UUID REFERENCES datasets(id),
    target_dataset_id UUID REFERENCES datasets(id),
    pipeline_id UUID REFERENCES pipelines(id),
    edge_type VARCHAR(50) NOT NULL,
    transformation JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_lineage_source_target CHECK (source_dataset_id IS NOT NULL OR target_dataset_id IS NOT NULL)
);

-- =============================================
-- APPROVALS
-- =============================================
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    requester_id UUID NOT NULL REFERENCES users(id),
    resource_type VARCHAR(50) NOT NULL CHECK (resource_type IN ('dataset','pipeline','access_request','policy_exception')),
    resource_id UUID NOT NULL,
    action_requested VARCHAR(50) NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','cancelled','expired')),
    decided_by UUID REFERENCES users(id),
    decided_at TIMESTAMPTZ,
    decision_comment TEXT,
    expires_at TIMESTAMPTZ,
    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================
-- AUDIT & EVIDENCE
-- =============================================
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    actor_user_id UUID REFERENCES users(id),
    actor_subject VARCHAR(255) NOT NULL,
    actor_ip INET,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    outcome VARCHAR(20) NOT NULL CHECK (outcome IN ('success','failure','denied')),
    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
    session_id VARCHAR(128),
    user_agent TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE evidence_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    evidence_type VARCHAR(100) NOT NULL,
    evidence_id_ref VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    storage_ref VARCHAR(1024) NOT NULL,
    checksum_sha256 VARCHAR(64),
    review_date TIMESTAMPTZ,
    review_due_date TIMESTAMPTZ,
    retention_until TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived','expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================
-- INDEXES
-- =============================================
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_datasets_domain ON datasets(organization_id, domain_id);
CREATE INDEX idx_datasets_status ON datasets(status);
CREATE INDEX idx_datasets_classification ON datasets(classification);
CREATE INDEX idx_pipeline_runs_status_started ON pipeline_runs(status, started_at);
CREATE INDEX idx_quality_results_run ON quality_results(run_id, checked_at);
CREATE INDEX idx_audit_events_org_time ON audit_events(organization_id, occurred_at DESC);
CREATE INDEX idx_audit_events_actor ON audit_events(actor_subject, occurred_at DESC);
CREATE INDEX idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX idx_approval_requests_status ON approval_requests(status, created_at);
CREATE INDEX idx_lineage_source ON data_lineage_edges(source_dataset_id);
CREATE INDEX idx_lineage_target ON data_lineage_edges(target_dataset_id);

-- =============================================
-- COMMENTS
-- =============================================
COMMENT ON TABLE audit_events IS 'Immutable audit trail. Restrict UPDATE/DELETE via DB permissions.';
COMMENT ON TABLE evidence_records IS 'Compliance evidence registry linked to ISO controls.';
COMMENT ON TABLE user_roles IS 'RBAC assignments with scope and optional expiry.';
COMMENT ON TABLE data_lineage_edges IS 'Data lineage graph edges between datasets/pipelines.';
