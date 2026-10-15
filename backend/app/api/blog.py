"""Public blog post endpoints for the knowledge hub."""
import logging
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.blog_post import BlogPost, STATUS_PUBLISHED
from backend.app.models.tag import Tag
from backend.app.schemas import BlogPostResponse, BlogPostListResponse
from backend.database import get_db
from backend.app.utils.time import utcnow

logger = logging.getLogger(__name__)

router = APIRouter()
public_router = APIRouter()


def _to_response(
    post: BlogPost,
    author_name: Optional[str],
    tag_names: List[str],
) -> BlogPostResponse:
    return BlogPostResponse(
        id=post.id,
        author_id=post.author_id,
        tenant_id=post.tenant_id,
        title=post.title,
        slug=post.slug,
        excerpt=post.excerpt,
        content=post.content,
        featured_image_url=post.featured_image_url,
        category=post.category,
        read_time=post.read_time,
        view_count=post.view_count,
        is_published=post.is_published,
        status=post.status,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author_name=author_name,
        tag_names=tag_names or [],
        tag_ids=[str(t.id) for t in (post.tags or [])],
    )


async def _serialize(post: BlogPost) -> BlogPostResponse:
    author_name = post.author.full_name if post.author else None
    tag_names = [t.name for t in (post.tags or [])]
    return _to_response(post, author_name, tag_names)


async def _fetch_published_posts(
    db: AsyncSession,
    limit: int,
    offset: int,
    category: Optional[str] = None,
    tag: Optional[str] = None,
) -> tuple[List[BlogPost], int]:
    query = (
        select(BlogPost)
        .where(
            BlogPost.status == STATUS_PUBLISHED,
            BlogPost.is_published.is_(True),
        )
        .order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        .limit(limit + 1)
        .offset(offset)
        .options(selectinload(BlogPost.author), selectinload(BlogPost.tags))
    )
    if category:
        query = query.where(BlogPost.category == category)
    if tag:
        query = query.where(BlogPost.tags.any(Tag.name == tag))
    result = await db.execute(query)
    posts = result.scalars().all()
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:-1]

    count_query = (
        select(func.count())
        .select_from(BlogPost)
        .where(
            BlogPost.status == STATUS_PUBLISHED,
            BlogPost.is_published.is_(True),
        )
    )
    if category:
        count_query = count_query.where(BlogPost.category == category)
    if tag:
        count_query = count_query.where(BlogPost.tags.any(Tag.name == tag))
    total = (await db.execute(count_query)).scalar_one()

    return posts, total


@public_router.get("/posts", response_model=BlogPostListResponse)
async def list_posts(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    slug: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List published blog posts visible to anonymous visitors."""
    posts, total = await _fetch_published_posts(db, limit, offset, category, slug)
    responses = [await _serialize(p) for p in posts]
    return BlogPostListResponse(
        posts=responses,
        total=total,
        page=(offset // limit) + 1 if limit else 1,
        page_size=len(responses),
    )


@public_router.get("/posts/{slug}", response_model=BlogPostResponse)
async def get_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single published blog post by slug (public)."""
    result = await db.execute(
        select(BlogPost)
        .where(
            BlogPost.slug == slug,
            BlogPost.status == STATUS_PUBLISHED,
            BlogPost.is_published.is_(True),
        )
        .options(selectinload(BlogPost.author), selectinload(BlogPost.tags))
    )
    post = result.scalars().first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return await _serialize(post)


async def seed_default_posts(db: AsyncSession) -> None:
    """Seed published blog posts with tags if the table is empty."""
    count = (await db.execute(select(func.count()).select_from(BlogPost))).scalar_one()
    if count > 0:
        return

    from backend.app.models.tenant import Tenant
    from backend.app.models.user import User, UserRole
    from backend.app.security import hash_password

    result = await db.execute(select(Tenant).where(Tenant.is_active.is_(True)).limit(1))
    tenant = result.scalars().first()

    if tenant is None:
        tenant = Tenant(
            name="DataAir Knowledge",
            slug="knowledge",
            description="Default knowledge hub tenant",
            is_active=True,
        )
        db.add(tenant)
        await db.flush()

    result = await db.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == "admin@dataair.io")
    )
    author = result.scalars().first()
    if author is None:
        author = User(
            tenant_id=tenant.id,
            email="admin@dataair.io",
            hashed_password=hash_password("admin123"),
            full_name="DataAir Team",
            is_active=True,
            is_superuser=True,
            role=UserRole.ADMIN,
        )
        db.add(author)
        await db.flush()

    tag_names = [
        "Data Engineering",
        "AI",
        "Tutorial",
        "Architecture",
        "Governance",
    ]
    created_tags: dict[str, Tag] = {}
    for name in tag_names:
        result = await db.execute(select(Tag).where(Tag.name == name))
        existing = result.scalars().first()
        if existing:
            created_tags[name] = existing
        else:
            tag = Tag(
                name=name,
                slug=name.lower().replace(" ", "-"),
                color="#6366f1",
            )
            db.add(tag)
            await db.flush()
            created_tags[name] = tag

    now = utcnow()
    post_data = [
        {
            "title": "Building a Vector Search Pipeline with DataAir",
            "slug": "building-vector-search-pipeline",
            "excerpt": "A deep-dive into how DataAir materialises documents into embeddable chunks and indexes them across vector and keyword stores for hybrid retrieval.",
            "content": "# Building a Vector Search Pipeline\n\nModern RAG applications depend on fast, accurate retrieval across mixed data types. This post walks through the five-stage pipeline: extract, clean, chunk, embed, and index.\n\n## 1. Data Extract\n\nRaw text is pulled from PDFs, HTML and object-store files, then normalised for encoding.\n\n## 2. Data Clean\n\nMarkup and boilerplate are stripped so downstream chunks carry signal rather than layout noise.\n\n## 3. Data Chunk\n\nLong text is split into overlapping token windows so no single answer depends on one huge block.\n\n## 4. Data Embed\n\nEach chunk is turned into a normalised vector using a configurable provider or the offline fallback.\n\n## 5. Data Index\n\nChunks are stored across the keyword, vector and graph indexes so hybrid retrieval can combine them.",
            "category": "Data Engineering",
            "read_time": 8,
            "tag": "Data Engineering",
        },
        {
            "title": "How Hybrid Search Ranks Results Better Than Pure Vector",
            "slug": "hybrid-search-ranking-explained",
            "excerpt": "Combining BM25 keyword scoring with vector similarity gives more relevant top-K results. Here is the math behind the fusion and why it matters for your knowledge bases.",
            "content": "# How Hybrid Search Ranks Results\n\nHybrid search fuses keyword (BM25) and vector similarity scores. The weighted sum means exact-term matches boost recall while embeddings capture semantic intent.\n\n## Fusion Formula\n\n```\nscore = alpha * bm25 + (1 - alpha) * vector_sim\n```\n\n## When to Use Each\n\n- BM25 excels at exact matches and boolean filters.\n- Vector similarity captures paraphrased queries.\n- Combining them reduces false negatives.",
            "category": "AI",
            "read_time": 6,
            "tag": "AI",
        },
        {
            "title": "Running DataAir Locally with Docker Compose",
            "slug": "running-dataair-locally",
            "excerpt": "Spin up the full stack—PostgreSQL with pgvector, Redis, Elasticsearch, Qdrant, MinIO, and the API—with a single command and start ingesting data in minutes.",
            "content": "# Running DataAir Locally\n\nThe entire stack is defined in `docker-compose.yml`. Run:\n\n```\ndocker compose up -d\n```\n\nServices brought up:\n- PostgreSQL 16 (with pgvector)\n- Redis\n- Elasticsearch\n- Qdrant\n- MinIO\n- API (FastAPI)",
            "category": "Tutorial",
            "read_time": 5,
            "tag": "Tutorial",
        },
        {
            "title": "Data Lineage: From Source to Answer",
            "slug": "data-lineage-source-to-answer",
            "excerpt": "Trace every asset from ingestion through transformation to the AI agents that consumed it. Learn how DataAir captures and visualises the full data journey.",
            "content": "# Data Lineage\n\nDataAir captures lineage at every stage:\n\n1. **Connect** — sources register their schema.\n2. **Ingest** — syncs tag datasets with the source run.\n3. **Curate** — pipelines record transformations.\n4. **Serve** — RAG endpoints cite which chunks were retrieved.\n\nThis produces an auditable graph from raw table to final answer.",
            "category": "Architecture",
            "read_time": 7,
            "tag": "Architecture",
        },
        {
            "title": "Governance as Code: Policy-Driven Data Access",
            "slug": "governance-as-code-policy-driven-access",
            "excerpt": "Define access policies as code, route changes through an approval queue, and maintain an immutable audit trail scoped by role per workspace.",
            "content": "# Governance as Code\n\nPolicies are defined as Python classes and stored as JSON. Each policy is evaluated at query time against the caller's role and tenant context.\n\n## Example Policy\n\n```python\nclass PIIAccessPolicy:\n    def can_read(self, user, column):\n        return user.role == \"admin\" or not column.is_pii\n```\n\n## Audit Trail\n\nEvery policy evaluation is logged with the request ID, user, and timestamp.",
            "category": "Governance",
            "read_time": 9,
            "tag": "Governance",
        },
        {
            "title": "Orchestrating RAG Pipelines with Apache Airflow",
            "slug": "orchestrating-rag-pipelines-with-airflow",
            "excerpt": "Define repeatable data pipelines that extract, clean, chunk, embed and index documents on schedule. Track each run for audit and quality regression.",
            "content": "# Orchestrating RAG Pipelines\n\nAirflow DAGs define the full document lifecycle:\n\n1. **ExtractOperator** pulls files from sources.\n2. **CleanOperator** normalises text.\n3. **ChunkOperator** splits into overlapping windows.\n4. **EmbedOperator** generates vectors.\n5. **IndexOperator** stores in vector + keyword indexes.\n\nEach operator emits metrics that are compared against an evaluation dataset.",
            "category": "AI",
            "read_time": 10,
            "tag": "AI",
        },
        {
            "title": "API Keys: Scoping, Expiry, and Usage Tracking",
            "slug": "api-keys-scoping-expiry-usage",
            "excerpt": "Learn how DataAir scopes API keys to read, write, or admin actions, stores them as HMAC digests, and logs per-request usage against your plan.",
            "content": "# API Keys\n\nDataAir API keys carry fine-grained scopes:\n\n- **read** — query knowledge bases and search.\n- **write** — add documents and trigger syncs.\n- **admin** — manage keys, profiles, and tenants.\n\nKeys are stored as HMAC digests and can carry an expiry date. Usage is logged per request and surfaced in the billing dashboard.",
            "category": "Data Engineering",
            "read_time": 4,
            "tag": "Data Engineering",
        },
        {
            "title": "Evaluating RAG Quality: Datasets and Metrics",
            "slug": "evaluating-rag-quality-datasets-and-metrics",
            "excerpt": "Score retrieval accuracy on your own datasets. This post covers how to create evaluation datasets, run automated checks, and detect quality regressions before they compound.",
            "content": "# Evaluating RAG Quality\n\nDataAir provides evaluation datasets to measure retrieval quality:\n\n- **Precision@K** — fraction of relevant results in the top-K.\n- **Recall@K** — fraction of relevant results retrieved.\n- **MRR** — mean reciprocal rank.\n\nYou can upload a dataset of queries with expected answers, run it against your knowledge base, and track metrics over time.",
            "category": "AI",
            "read_time": 6,
            "tag": "AI",
        },
    ]

    for i, pd in enumerate(post_data):
        tags = [created_tags[pd["tag"]]] if pd["tag"] in created_tags else []
        post = BlogPost(
            tenant_id=tenant.id,
            author_id=author.id,
            title=pd["title"],
            slug=pd["slug"],
            excerpt=pd["excerpt"],
            content=pd["content"],
            category=pd["category"],
            read_time=pd["read_time"],
            is_published=True,
            status=STATUS_PUBLISHED,
            published_at=now - timedelta(hours=len(post_data) - i),
            tags=tags,
        )
        db.add(post)

    await db.flush()
