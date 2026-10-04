# DataAir Development Guide

## Getting Started

### Prerequisites

- Docker 24+ & Docker Compose 2+
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)
- PostgreSQL 16+ (via Docker)
- Redis 7+ (via Docker)
- MinIO (via Docker)
- Make (optional, for shortcuts)

### Quick Start

```bash
# Clone and enter
cd dataair

# Copy environment template
cp .env.example .env

# Start all services
docker compose up -d

# Run migrations
docker compose exec backend alembic upgrade head

# Verify health
curl http://localhost:8000/health
curl http://localhost:3000/api/health
```

## Project Structure

```
dataair/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes (v1)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── dependencies/   # FastAPI dependencies
│   │   └── security/       # Auth, encryption
│   ├── config.py           # Configuration
│   ├── database.py         # DB session management
│   ├── main.py             # App entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js application
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── lib/                # Utilities
│   ├── hooks/              # Custom hooks
│   ├── Dockerfile
│   └── package.json
├── docker/
│   ├── init.sql           # DB initialization
│   └── nginx.conf         # Reverse proxy (prod)
├── docs/                   # Documentation
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

## Development Workflow

### Backend Development

```bash
# Enter backend container
docker compose exec backend bash

# Or run locally with venv
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/ -v

# Run with auto-reload (local)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
# Enter frontend container
docker compose exec frontend bash

# Or run locally
cd frontend
npm install
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint
npm run lint
```

### Database Operations

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U dataair -d dataair

# Run raw SQL
docker compose exec postgres psql -U dataair -d dataair -c "SELECT * FROM users;"

# Backup
docker compose exec postgres pg_dump -U dataair dataair > backup.sql

# Restore
docker compose exec -T postgres psql -U dataair dataair < backup.sql
```

### Redis Operations

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# Monitor commands
docker compose exec redis redis-cli MONITOR

# Clear cache
docker compose exec redis redis-cli FLUSHALL
```

### MinIO Operations

```bash
# Access MinIO Console: http://localhost:9001
# User: minioadmin / Password: minioadmin

# Using mc CLI
docker run --rm -it --network dataair_default minio/mc \
  alias set local http://minio:9000 minioadmin minioadmin
```

## Coding Standards

### Python (Backend)

- **Formatter**: Black (line length 100)
- **Import sorter**: isort
- **Type checker**: mypy (strict mode)
- **Linter**: ruff
- **Testing**: pytest + pytest-asyncio

```bash
# Format
black backend/
isort backend/

# Type check
mypy backend/

# Lint
ruff check backend/

# Test
pytest backend/tests/ -v --cov=backend
```

### TypeScript (Frontend)

- **Formatter**: Prettier
- **Linter**: ESLint (Next.js config)
- **Type checker**: tsc --noEmit

```bash
# Format
npm run format

# Lint
npm run lint

# Type check
npm run typecheck
```

### Git Workflow

```bash
# Feature branch
git checkout -b feature/phase-4-connectors

# Commit with conventional commits
git commit -m "feat(connectors): add PostgreSQL connector"

# Push and create PR
git push origin feature/phase-4-connectors
```

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

## Testing Strategy

### Test Pyramid

```
         E2E Tests (Playwright)
        /                       \
   Integration Tests (pytest)   UI Tests (React Testing Library)
      /           \             /             \
 Unit Tests    Unit Tests   Unit Tests     Unit Tests
(pytest)      (jest)        (pytest)       (jest)
```

### Backend Testing

```python
# Unit test example
async def test_user_creation(db_session):
    user = UserFactory.create(email="test@example.com")
    assert user.email == "test@example.com"

# Integration test example
async def test_register_endpoint(async_client):
    response = await async_client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()
```

### Frontend Testing

Tests live in `frontend/__tests__/` and run on Jest with Testing Library.
`jest.config.js` maps the `@/` alias, compiles JSX for Node, and `jest.setup.ts`
lends jsdom the streaming primitives that `fetch` responses use.

```tsx
// Component test example
import { render, screen } from '@testing-library/react'
import { LoginForm } from '@/components/auth/LoginForm'

test('renders login form', () => {
  render(<LoginForm />)
  expect(screen.getByLabelText('Email')).toBeInTheDocument()
  expect(screen.getByLabelText('Password')).toBeInTheDocument()
})
```

```bash
npm test              # jest
npm run test:watch    # jest --watch
npm run test:coverage # jest --coverage
npm run lint          # next lint (eslint-config-next)
```

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# E2E
make test-e2e

# Coverage
make coverage
```

Backend tests never call a real model. `tests/conftest.py` pins the gateway to
the offline provider, so the suite is fast and passes without any API key:

```bash
pytest tests/ -q                    # 27 tests, ~2s
python tests/test_platform.py       # the pipeline checks as a standalone script
```

### Timestamps

`backend/app/utils/time.py` owns the timestamp convention. Columns are plain
`TIMESTAMP WITHOUT TIME ZONE` and asyncpg rejects offset-aware datetimes, so
application code stores naive UTC via `utcnow()`. Do not call
`datetime.now(timezone.utc)` for a value that reaches the database — JWT
expiry math in `backend/app/security.py` is the one deliberate exception.
Migrating to `timestamptz` is a one-place change once it happens.

## Environment Variables

### Required (.env)

```env
# Application
APP_ENV=development
DEBUG=true
APP_NAME=DataAir
APP_VERSION=1.0.0

# Database
DATABASE_URL=postgresql+asyncpg://dataair:dataair@postgres:5432/dataair
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET=dataair

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# Qdrant
QDRANT_URL=http://qdrant:6333

# JWT
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# CSRF
CSRF_SECRET_KEY=your-csrf-secret-min-32-chars

# API Key
API_KEY_HMAC_SECRET=your-api-key-secret-min-32-chars

# Frontend
FRONTEND_URL=http://localhost:3000
PUBLIC_BASE_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000

# Cookies
COOKIE_SECURE=false
COOKIE_SAMESITE=lax

# LLM (optional for dev)
# Every provider is optional. DataAir answers with the first configured one and
# degrades to a deterministic offline assistant when none is available.
# Pin one provider with LLM_PROVIDER, or leave it empty to auto-select.
LLM_PROVIDER=
LLM_OFFLINE_FALLBACK=true
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-haiku-4-5
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
OLLAMA_BASE_URL=
OLLAMA_MODEL=llama3.2
LLM_MODEL=gpt-4o
LLM_EMBEDDING_MODEL=text-embedding-3-small

# Homepage chat
CHAT_SYSTEM_PROMPT=
CHAT_TEMPERATURE=0.4
CHAT_MAX_TOKENS=1024
CHAT_RATE_LIMIT_REQUESTS=20
CHAT_RATE_LIMIT_WINDOW_SECONDS=60

# Admin
ADMIN_EMAILS=admin@example.com
```

### Production Additions

```env
APP_ENV=production
DEBUG=false
DATABASE_ECHO=false
COOKIE_SECURE=true
COOKIE_SAMESITE=none
MINIO_SECURE=true
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_FREE_PRICE_ID=
STRIPE_PRO_PRICE_ID=
STRIPE_ENTERPRISE_PRICE_ID=
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add data_sources table"

# Manual migration
alembic revision -m "add index on data_sources"
```

### Migration Best Practices

1. **Always review auto-generated migrations**
2. **Test upgrade AND downgrade**
3. **Use batch operations for large tables**
4. **Add indexes in separate migrations**
5. **Never modify applied migrations**

### Migration Template

```python
"""add data_sources table

Revision ID: abc123
Revises: def456
Create Date: 2026-01-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )
    op.create_index('ix_data_sources_tenant_id', 'data_sources', ['tenant_id'])

def downgrade():
    op.drop_index('ix_data_sources_tenant_id', 'data_sources')
    op.drop_table('data_sources')
```

## API Development

### Route Structure

```python
# backend/app/api/v1/connectors.py
from fastapi import APIRouter, Depends, HTTPException
from backend.app.schemas import ConnectorCreate, ConnectorResponse
from backend.app.dependencies import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/connectors", tags=["Connectors"])

@router.post("/", response_model=ConnectorResponse)
async def create_connector(
    connector: ConnectorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Implementation
    pass
```

### Schema Definition

```python
# backend/app/schemas/connector.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class ConnectorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(..., pattern="^(postgresql|mysql|csv|json|excel|rest_api|minio)$")
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class ConnectorCreate(ConnectorBase):
    pass

class ConnectorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ConnectorResponse(ConnectorBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Error Handling

```python
# backend/app/api/errors.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        }
    )

async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail.get("code", "ERROR") if isinstance(exc.detail, dict) else "ERROR",
                "message": exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail),
                "details": exc.detail.get("details") if isinstance(exc.detail, dict) else None
            }
        }
    )
```

## Service Layer Patterns

### Connector Interface

```python
# backend/app/services/connectors/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, AsyncIterator
from dataclasses import dataclass

@dataclass
class ConnectionResult:
    success: bool
    message: str
    details: Dict[str, Any] = None

@dataclass
class SchemaInfo:
    tables: List[Dict[str, Any]]
    columns: Dict[str, List[Dict[str, Any]]]

class DataConnector(ABC):
    """Base interface for all data connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def connect(self) -> ConnectionResult:
        """Establish and verify connection"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> ConnectionResult:
        """Test if connection works"""
        pass
    
    @abstractmethod
    async def discover_schema(self) -> SchemaInfo:
        """Discover source schema"""
        pass
    
    @abstractmethod
    async def extract(self, source_id: str, incremental: bool = False) -> AsyncIterator[Dict[str, Any]]:
        """Extract data records"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ConnectionResult:
        """Health check for monitoring"""
        pass
```

### Processor Interface

```python
# backend/app/services/processing/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import polars as pl

@dataclass
class ValidationResult:
    valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

class DataProcessor(ABC):
    """Base interface for data processors"""
    
    @abstractmethod
    async def validate(self, df: pl.DataFrame) -> ValidationResult:
        """Validate data quality"""
        pass
    
    @abstractmethod
    async def clean(self, df: pl.DataFrame) -> pl.DataFrame:
        """Clean data (handle nulls, duplicates, etc.)"""
        pass
    
    @abstractmethod
    async def transform(self, df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
        """Apply transformations"""
        pass
```

## Frontend Patterns

### API Client

```typescript
// frontend/lib/api/client.ts
import { createApiClient } from '@tanstack/react-query'

export const api = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  // Auto-attach auth token
  prepareHeaders: (headers, { getState }) => {
    const token = getState().auth.accessToken
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    return headers
  },
})
```

### React Query Hooks

```typescript
// frontend/hooks/useConnectors.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api/client'
import type { Connector, ConnectorCreate } from '@/types/connector'

export function useConnectors() {
  return useQuery({
    queryKey: ['connectors'],
    queryFn: () => api.get<Connector[]>('/connectors'),
  })
}

export function useCreateConnector() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ConnectorCreate) => api.post<Connector>('/connectors', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
    },
  })
}
```

### Component Structure

```tsx
// frontend/components/connectors/ConnectorCard.tsx
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Connector } from '@/types/connector'

interface ConnectorCardProps {
  connector: Connector
  onEdit: (id: string) => void
  onDelete: (id: string) => void
}

export function ConnectorCard({ connector, onEdit, onDelete }: ConnectorCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h3 className="font-semibold">{connector.name}</h3>
          <Badge variant={connector.is_active ? 'default' : 'secondary'}>
            {connector.source_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {connector.config?.host || 'File-based'}
        </p>
        <div className="flex gap-2 mt-4">
          <Button variant="outline" size="sm" onClick={() => onEdit(connector.id)}>
            Edit
          </Button>
          <Button variant="destructive" size="sm" onClick={() => onDelete(connector.id)}>
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

## Debugging

### Backend Debugging

```bash
# View logs
docker compose logs -f backend

# Debug with pdb (add to code)
import pdb; pdb.set_trace()

# Or use debugpy for VS Code
# In Dockerfile: pip install debugpy
# python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn backend.main:app
```

### Frontend Debugging

```bash
# View logs
docker compose logs -f frontend

# React DevTools in browser
# Console logging available
```

### Database Debugging

```bash
# Query execution plans
EXPLAIN ANALYZE SELECT * FROM data_sources WHERE tenant_id = '...';

# Check locks
SELECT * FROM pg_locks WHERE NOT granted;

# Check connections
SELECT * FROM pg_stat_activity;
```

## Performance Profiling

### Backend

```python
# Add to code for profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... code to profile ...

profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats(20)
```

### Database

```sql
-- Enable pg_stat_statements
CREATE EXTENSION pg_stat_statements;

-- Top queries by time
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;
```

## Deployment

### Staging

```bash
# Build images
docker compose -f docker-compose.yml -f docker-compose.staging.yml build

# Deploy
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Run migrations
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec backend alembic upgrade head
```

### Production

```bash
# Use production compose file
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Change ports in docker-compose.yml or stop conflicting services |
| DB connection refused | Wait for postgres health check, check DATABASE_URL |
| Migration fails | Check migration file, run `alembic current` |
| Frontend can't reach API | Check ALLOWED_ORIGINS, FRONTEND_URL, network |
| MinIO access denied | Check credentials, bucket policy |
| Redis connection error | Check REDIS_URL, Redis container health |
| Permission denied | Check tenant_id in queries, user roles |

### Log Locations

```bash
# Application logs (stdout/stderr)
docker compose logs backend
docker compose logs frontend
docker compose logs worker

# Database logs
docker compose logs postgres

# Nginx logs (production)
docker compose logs nginx
```

## Useful Commands

```bash
# Full reset
make clean && make up

# Rebuild specific service
docker compose build --no-cache backend && docker compose up -d backend

# Shell into container
docker compose exec backend bash
docker compose exec frontend sh
docker compose exec postgres psql -U dataair -d dataair

# View resource usage
docker stats

# Prune unused
docker system prune -a
```

## Contributing

1. Read this guide and `docs/architecture.md`
2. Check `docs/roadmap.md` for current phase
3. Pick a task from the current phase
4. Create feature branch
5. Implement with tests
6. Run full test suite
7. Submit PR with description

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/)
- [React Query Docs](https://tanstack.com/query/latest)
- [shadcn/ui Docs](https://ui.shadcn.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Docker Compose Spec](https://docs.docker.com/compose/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Redis Docs](https://redis.io/documentation)
- [MinIO Docs](https://min.io/docs/minio/linux/index.html)