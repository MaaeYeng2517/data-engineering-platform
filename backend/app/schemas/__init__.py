"""Pydantic schemas for API requests and responses."""
import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from backend.app.models.api_key import ApiKeyScope
from backend.app.models.billing import SubscriptionStatus
from backend.app.models.contact import ContactStatus
from backend.app.models.profile import (
    AuthType,
    CloudProvider,
    ProfileEnvironment,
    ServiceHealth,
    ServiceType,
)
from backend.app.models.user import UserRole
from backend.app.models.work_group import WorkGroupRole
from backend.config import CHAT_MAX_MESSAGE_CHARS, CHAT_MAX_MESSAGES


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: Optional[str]
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    tenant_id: Optional[UUID] = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: str
    user: UserResponse


class MembershipPlanCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    price_cents: int = Field(0, ge=0)
    currency: str = Field("thb", min_length=3, max_length=3)
    interval: str = Field("month", pattern="^(month|year)$")
    api_calls_per_month: int = Field(1000, ge=0)
    features: List[str] = Field(default_factory=list)
    is_active: bool = True
    sort_order: int = Field(0, ge=0)


class MembershipPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    stripe_price_id: Optional[str]
    stripe_product_id: Optional[str]
    name: str
    description: Optional[str]
    price_cents: int
    currency: str
    interval: str
    api_calls_per_month: int
    features: List[str]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SubscriptionCreate(BaseModel):
    plan_id: UUID
    stripe_payment_method_id: Optional[str] = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    plan_id: UUID
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    stripe_price_id: Optional[str]
    status: SubscriptionStatus
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    metadata: Dict[str, Any] = Field(alias="data", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime


class SubscriptionUpdate(BaseModel):
    cancel_at_period_end: Optional[bool] = None


class StripeCheckoutRequest(BaseModel):
    plan_id: UUID
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class StripeCheckoutResponse(BaseModel):
    checkout_url: Optional[str] = None
    session_id: Optional[str] = None
    message: Optional[str] = None


class StripePortalRequest(BaseModel):
    return_url: Optional[str] = None


class StripePortalResponse(BaseModel):
    portal_url: str


class EntitlementResponse(BaseModel):
    plan: str
    status: str
    api_calls_limit: int
    features: List[str]
    current_period_end: Optional[datetime] = None


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: List[ApiKeyScope] = Field(default_factory=lambda: [ApiKeyScope.READ])
    expires_at: Optional[datetime] = None

    @field_validator("scopes")
    @classmethod
    def unique_scopes(cls, value: List[ApiKeyScope]) -> List[ApiKeyScope]:
        return list(dict.fromkeys(value))


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    tenant_id: UUID
    name: str
    key_prefix: str
    scopes: List[ApiKeyScope]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyResponse
    plain_key: str


class ApiUsageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    api_key_id: UUID
    user_id: UUID
    tenant_id: UUID
    endpoint: str
    method: str
    status_code: Optional[int]
    request_size: Optional[int]
    response_size: Optional[int]
    latency_ms: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    error_message: Optional[str]
    created_at: datetime


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=10000)


class ContactMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID]
    tenant_id: Optional[UUID]
    name: str
    email: str
    subject: str
    message: str
    status: ContactStatus
    admin_notes: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    updated_at: datetime


class ContactMessageUpdate(BaseModel):
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = None


class AdminStatsResponse(BaseModel):
    total_users: int
    total_tenants: int
    total_subscriptions: int
    active_subscriptions: int
    total_api_keys: int
    active_api_keys: int
    total_api_calls_today: int
    total_api_calls_month: int
    revenue_cents: int
    contact_messages: int
    pending_contact_messages: int


class AdminUserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class AdminTenantListResponse(BaseModel):
    tenants: List[TenantResponse]
    total: int
    page: int
    page_size: int


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    owner_id: UUID
    name: str
    description: Optional[str]
    slug: str
    settings: Dict[str, Any]
    is_published: bool
    status: str
    version: str
    created_at: datetime
    updated_at: datetime


class DocumentCreate(BaseModel):
    kb_id: UUID
    title: str
    source_type: str
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kb_id: UUID
    title: str
    source_type: str
    source_url: Optional[str]
    status: str
    version: str
    is_published: bool
    created_at: datetime


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    token_count: Optional[int]
    metadata: Dict[str, Any]


class SearchRequest(BaseModel):
    query: str
    kb_ids: List[UUID]
    metadata_filters: Optional[Dict[str, Any]] = None
    limit: int = Field(10, ge=1, le=100)
    score_threshold: Optional[float] = None
    search_type: str = "hybrid"


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    content: str
    score: float
    metadata: Dict[str, Any]
    sources: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    latency_ms: float


class RAGRequest(BaseModel):
    query: str
    kb_ids: List[UUID]
    metadata_filters: Optional[Dict[str, Any]] = None
    limit: int = Field(5, ge=1, le=20)
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(1000, ge=1, le=10000)


class RAGResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    citations: List[Dict[str, Any]]
    latency_ms: float
    token_usage: Dict[str, int]


class ChatTurn(BaseModel):
    """One conversation turn from a client. The server owns the system prompt."""

    role: str = Field("user", pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=CHAT_MAX_MESSAGE_CHARS)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("content must not be blank")
        return cleaned


class ChatRequest(BaseModel):
    """A chat turn, either as full history or as a single new message."""

    message: Optional[str] = Field(None, min_length=1, max_length=CHAT_MAX_MESSAGE_CHARS)
    messages: List[ChatTurn] = Field(default_factory=list, max_length=CHAT_MAX_MESSAGES)
    provider: Optional[str] = Field(None, max_length=32)
    model: Optional[str] = Field(None, max_length=128)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=8000)
    kb_ids: List[UUID] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be blank")
        return cleaned

    @model_validator(mode="after")
    def require_prompt(self) -> "ChatRequest":
        """A request needs either history or a new message to answer."""
        if self.message is None and not self.messages:
            raise ValueError("Provide 'message' or a non-empty 'messages' list")
        if self.message is None and self.messages[-1].role != "user":
            # A trailing user turn is required when no new message is appended,
            # because the providers have to be left with something to answer.
            raise ValueError("The last message must have role 'user'")
        return self

    def turns(self) -> List[ChatTurn]:
        """History followed by the new message, when one was sent separately."""
        turns = list(self.messages)
        if self.message:
            turns.append(ChatTurn(role="user", content=self.message))
        return turns


class ChatSource(BaseModel):
    """A retrieved passage used to ground an answer."""

    id: str
    title: Optional[str] = None
    snippet: str = ""
    score: float = 0.0


class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    finish_reason: str = "stop"
    latency_ms: float
    token_usage: Dict[str, int] = Field(default_factory=dict)
    sources: List[ChatSource] = Field(default_factory=list)
    degraded: bool = False


class ChatProviderInfo(BaseModel):
    """Discovery payload so a client can offer only working models."""

    name: str
    label: str
    configured: bool
    available: bool
    default_model: str
    models: List[str] = Field(default_factory=list)
    requires_key: bool = True


class ChatProvidersResponse(BaseModel):
    providers: List[ChatProviderInfo]
    default_provider: str
    default_model: str
    degraded: bool = False


class WorkflowCreate(BaseModel):
    kb_id: UUID
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kb_id: UUID
    name: str
    description: Optional[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    is_active: bool
    version: str


class MetadataSchemaCreate(BaseModel):
    kb_id: UUID
    name: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]]
    taxonomy: Dict[str, Any] = Field(default_factory=dict)


class MetadataSchemaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kb_id: UUID
    name: str
    description: Optional[str]
    fields: List[Dict[str, Any]]
    taxonomy: Dict[str, Any]
    is_active: bool


class EvaluationRequest(BaseModel):
    kb_id: UUID
    dataset_id: Optional[UUID] = None
    questions: Optional[List[Dict[str, Any]]] = None


class EvaluationResponse(BaseModel):
    run_id: UUID
    metrics: Dict[str, float]
    overall_score: float
    results: List[Dict[str, Any]]
    status: str


class WorkGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    slug: Optional[str] = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned


class WorkGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WorkGroupMemberAdd(BaseModel):
    user_id: UUID
    role: WorkGroupRole = WorkGroupRole.MEMBER


class WorkGroupMemberResponse(BaseModel):
    id: UUID
    work_group_id: UUID
    user_id: UUID
    role: WorkGroupRole
    joined_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None


class WorkGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    member_count: int = 0
    created_at: datetime
    updated_at: datetime


class WorkGroupDetailResponse(WorkGroupResponse):
    members: List[WorkGroupMemberResponse] = Field(default_factory=list)


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    environment: ProfileEnvironment = ProfileEnvironment.DEVELOPMENT
    cloud_provider: CloudProvider = CloudProvider.OTHER
    region: Optional[str] = Field(None, max_length=60)
    zone: Optional[str] = Field(None, max_length=60)
    variables: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    is_default: bool = False
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_profile_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: List[str]) -> List[str]:
        return [tag.strip() for tag in value if tag and tag.strip()]


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    environment: Optional[ProfileEnvironment] = None
    cloud_provider: Optional[CloudProvider] = None
    region: Optional[str] = Field(None, max_length=60)
    zone: Optional[str] = Field(None, max_length=60)
    variables: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ProfileServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    name: str
    service_type: str
    provider: Optional[str]
    description: Optional[str]
    api_base_url: Optional[str]
    host: Optional[str]
    port: Optional[int]
    region: Optional[str]
    zone: Optional[str]
    auth_type: str
    username: Optional[str]
    env_vars: Dict[str, Any]
    headers: Dict[str, Any]
    timeout_seconds: int
    max_retries: int
    health_check_url: Optional[str]
    health_check_enabled: bool
    health_status: str
    last_checked_at: Optional[datetime]
    is_active: bool
    # Secrets are never sent to a client; `has_token` says whether one is set
    # and `token_masked` previews it.
    has_token: bool = False
    has_credentials: bool = False
    token_masked: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    owner_id: UUID
    name: str
    slug: str
    description: Optional[str]
    environment: str
    cloud_provider: str
    region: Optional[str]
    zone: Optional[str]
    variables: Dict[str, Any]
    tags: List[str]
    is_default: bool
    is_active: bool
    service_count: int = 0
    config_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProfileDetailResponse(ProfileResponse):
    services: List[ProfileServiceResponse] = Field(default_factory=list)
    config_items: List["ProfileConfigItemResponse"] = Field(default_factory=list)


class ProfileServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    service_type: ServiceType = ServiceType.OTHER
    provider: Optional[str] = Field(None, max_length=80)
    description: Optional[str] = None
    api_base_url: Optional[str] = Field(None, max_length=500)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    region: Optional[str] = Field(None, max_length=60)
    zone: Optional[str] = Field(None, max_length=60)
    auth_type: AuthType = AuthType.API_KEY
    # Write-only. Stored encrypted and never echoed back.
    token: Optional[str] = None
    username: Optional[str] = Field(None, max_length=255)
    credentials: Optional[Dict[str, Any]] = None
    env_vars: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(30, ge=1, le=600)
    max_retries: int = Field(3, ge=0, le=10)
    health_check_url: Optional[str] = Field(None, max_length=500)
    health_check_enabled: bool = False
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_service_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned

    @model_validator(mode="after")
    def require_an_endpoint(self) -> "ProfileServiceCreate":
        if not (self.api_base_url or self.host):
            raise ValueError("api_base_url or host is required")
        return self


class ProfileServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    service_type: Optional[ServiceType] = None
    provider: Optional[str] = Field(None, max_length=80)
    description: Optional[str] = None
    api_base_url: Optional[str] = Field(None, max_length=500)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    region: Optional[str] = Field(None, max_length=60)
    zone: Optional[str] = Field(None, max_length=60)
    auth_type: Optional[AuthType] = None
    # Supplying a token rotates it; omit the field to keep the stored one.
    token: Optional[str] = None
    clear_token: bool = False
    username: Optional[str] = Field(None, max_length=255)
    credentials: Optional[Dict[str, Any]] = None
    env_vars: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=600)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    health_check_url: Optional[str] = Field(None, max_length=500)
    health_check_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class ProfileServiceSecretResponse(BaseModel):
    """Plaintext secrets, reachable only through the admin reveal endpoint."""

    token: Optional[str] = None
    credentials: Dict[str, Any] = Field(default_factory=dict)


class ProfileConfigItemCreate(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: Optional[str] = None
    description: Optional[str] = None
    value_type: str = Field("string", max_length=20)
    is_secret: bool = False
    tags: List[str] = Field(default_factory=list)

    @field_validator("key")
    @classmethod
    def strip_config_key(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("key must not be blank")
        return cleaned

    @field_validator("value_type")
    @classmethod
    def validate_value_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"string", "number", "boolean", "json"}:
            raise ValueError("value_type must be string, number, boolean or json")
        return cleaned

    @field_validator("tags")
    @classmethod
    def clean_item_tags(cls, value: List[str]) -> List[str]:
        return [tag.strip() for tag in value if tag and tag.strip()]


class ProfileConfigItemUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    value_type: Optional[str] = Field(None, max_length=20)
    is_secret: Optional[bool] = None
    tags: Optional[List[str]] = None


class ProfileConfigItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    key: str
    description: Optional[str]
    value_type: str
    is_secret: bool
    tags: List[str]
    # Secret values are withheld; `has_value` reports presence instead.
    value: Optional[str] = None
    value_masked: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileResolvedService(BaseModel):
    """A service as the platform would use it: endpoint plus a filled token."""

    id: UUID
    name: str
    service_type: str
    provider: Optional[str]
    api_base_url: Optional[str]
    host: Optional[str]
    port: Optional[int]
    region: Optional[str]
    zone: Optional[str]
    auth_type: str
    token: Optional[str] = None
    username: Optional[str] = None
    credentials: Dict[str, Any] = Field(default_factory=dict)
    env_vars: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int
    max_retries: int
    health_status: str
    is_active: bool


class ProfileResolvedResponse(BaseModel):
    """The effective configuration of a profile, flattened for consumers.

    Secret values are omitted. A caller that needs a real token reads it from
    the service it belongs to through the admin reveal endpoint.
    """

    profile: ProfileResponse
    variables: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Optional[str]] = Field(default_factory=dict)
    services: List[ProfileResolvedService] = Field(default_factory=list)


ProfileDetailResponse.model_rebuild()
