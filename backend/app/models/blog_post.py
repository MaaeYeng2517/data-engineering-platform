"""Blog post model for the platform knowledge base."""
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


# Blog post lifecycle: draft while being written, published once reviewed,
# archived when retired but kept for historical reference.
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    excerpt = Column(Text)
    content = Column(Text, nullable=False)
    featured_image_url = Column(Text)
    category = Column(String(50), default="AI")
    read_time = Column(Integer, default=5)  # minutes
    view_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    status = Column(String, default=STATUS_DRAFT)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    author = relationship("User", back_populates="blog_posts")
    tenant = relationship("Tenant", back_populates="blog_posts")
    tags = relationship("Tag", secondary="blog_post_tag_association", back_populates="blog_posts")

    def __repr__(self):
        return f"<BlogPost {self.title}>"


# Many-to-many with the existing Tag model.
from sqlalchemy import Table

blog_post_tag_association = Table(
    "blog_post_tag_association",
    Base.metadata,
    Column("tag_id", UUID, ForeignKey("tags.id"), primary_key=True),
    Column("blog_post_id", UUID, ForeignKey("blog_posts.id"), primary_key=True),
)