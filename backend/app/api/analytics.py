"""Website analytics API endpoints."""
import logging
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_optional_user
from backend.app.models.analytics import (
    AnalyticsEvent,
    PageView,
    Subscriber,
    SubscriberStatus,
    UsageEvent,
    Visitor,
)
from backend.app.models.user import User
from backend.app.schemas import (
    AnalyticsEventCreate,
    AnalyticsOverviewResponse,
    PageViewCreate,
    SubscriberCreate,
    SubscriberResponse,
    SubscriberStatsResponse,
    TrackEventResponse,
    VisitorTrackResponse,
    WebsiteStatsResponse,
)
from backend.database import get_db
from backend.app.utils.time import utcnow

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analytics/track", response_model=VisitorTrackResponse)
async def track_visitor(
    payload: PageViewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Track a page view and create/update visitor."""
    session_id = payload.session_id or str(uuid4())
    
    # Find or create visitor
    visitor = None
    if payload.visitor_id:
        result = await db.execute(select(Visitor).where(Visitor.id == payload.visitor_id))
        visitor = result.scalars().first()
    if not visitor and session_id:
        result = await db.execute(select(Visitor).where(Visitor.session_id == session_id))
        visitor = result.scalars().first()
    
    if not visitor:
        visitor = Visitor(
            session_id=session_id,
            tenant_id=user.tenant_id if user else payload.tenant_id,
            ip_address=request.client.host if request.client else payload.ip_address,
            user_agent=request.headers.get("user-agent") or payload.user_agent,
            referrer=payload.referrer,
            landing_page=payload.path,
            is_authenticated=user is not None,
            user_id=user.id if user else None,
            first_seen_at=utcnow(),
            last_seen_at=utcnow(),
            page_views_count=1,
        )
        db.add(visitor)
        await db.flush()
    else:
        visitor.last_seen_at = utcnow()
        visitor.page_views_count = (visitor.page_views_count or 0) + 1
        if user and not visitor.user_id:
            visitor.user_id = user.id
            visitor.is_authenticated = True
            visitor.tenant_id = user.tenant_id
        await db.flush()
    
    # Create page view
    page_view = PageView(
        visitor_id=visitor.id,
        user_id=user.id if user else None,
        tenant_id=visitor.tenant_id or (user.tenant_id if user else None),
        session_id=visitor.session_id,
        path=payload.path,
        referrer=payload.referrer,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_term=payload.utm_term,
        utm_content=payload.utm_content,
        duration_ms=payload.duration_ms,
        ip_address=request.client.host if request.client else payload.ip_address,
        user_agent=request.headers.get("user-agent") or payload.user_agent,
        created_at=utcnow(),
    )
    db.add(page_view)
    await db.commit()
    await db.refresh(visitor)
    
    return VisitorTrackResponse(
        visitor_id=visitor.id,
        session_id=visitor.session_id,
        page_view_id=page_view.id,
    )


@router.post("/analytics/events", response_model=TrackEventResponse)
async def track_event(
    payload: AnalyticsEventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Track an analytics event."""
    # Find visitor
    visitor = None
    if payload.visitor_id:
        result = await db.execute(select(Visitor).where(Visitor.id == payload.visitor_id))
        visitor = result.scalars().first()
    elif payload.session_id:
        result = await db.execute(select(Visitor).where(Visitor.session_id == payload.session_id))
        visitor = result.scalars().first()
    
    event = AnalyticsEvent(
        visitor_id=visitor.id if visitor else None,
        user_id=user.id if user else payload.user_id,
        tenant_id=visitor.tenant_id if visitor else (user.tenant_id if user else payload.tenant_id),
        session_id=payload.session_id or (visitor.session_id if visitor else None),
        event_type=payload.event_type,
        section=payload.section,
        feature=payload.feature,
        action=payload.action,
        path=payload.path,
        label=payload.label,
        value=payload.value,
        properties=payload.properties or {},
        referrer=payload.referrer,
        ip_address=request.client.host if request.client else payload.ip_address,
        user_agent=request.headers.get("user-agent") or payload.user_agent,
        duration_ms=payload.duration_ms,
        created_at=utcnow(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    return TrackEventResponse(event_id=event.id, success=True)


@router.post("/analytics/subscribers", response_model=SubscriberResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_newsletter(
    payload: SubscriberCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Subscribe to newsletter."""
    # Check if exists
    result = await db.execute(select(Subscriber).where(Subscriber.email == payload.email.lower()))
    existing = result.scalars().first()
    if existing:
        if existing.status == SubscriberStatus.UNSUBSCRIBED.value:
            existing.status = SubscriberStatus.ACTIVE.value
            existing.unsubscribed_at = None
            await db.commit()
            await db.refresh(existing)
            return existing
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already subscribed")
    
    subscriber = Subscriber(
        email=payload.email.lower(),
        name=payload.name,
        status=SubscriberStatus.ACTIVE.value,
        source=payload.source or "website",
        consent_given=True,
        consent_at=utcnow(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=payload.referrer,
        landing_page=payload.landing_page,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(subscriber)
    await db.commit()
    await db.refresh(subscriber)
    return subscriber


@router.get("/analytics/website-stats", response_model=WebsiteStatsResponse)
async def get_website_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive website statistics for charts."""
    end_date = utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Total stats
    total_visitors = await db.execute(select(func.count(Visitor.id)))
    total_visitors_count = total_visitors.scalar() or 0
    
    total_page_views = await db.execute(select(func.count(PageView.id)).where(PageView.created_at >= start_date))
    total_page_views_count = total_page_views.scalar() or 0
    
    total_subscribers = await db.execute(select(func.count(Subscriber.id)).where(Subscriber.status == SubscriberStatus.ACTIVE.value))
    total_subscribers_count = total_subscribers.scalar() or 0
    
    total_users = await db.execute(select(func.count(User.id)))
    total_users_count = total_users.scalar() or 0
    
    # Daily visitors (last N days)
    from sqlalchemy import text
    daily_visitors = await db.execute(text("SELECT date_trunc('day', first_seen_at) as d, count(*) as c FROM visitors WHERE first_seen_at >= :start GROUP BY date_trunc('day', first_seen_at) ORDER BY date_trunc('day', first_seen_at)"), {"start": start_date})
    daily_visitors_data = [{"date": str(row.d.date()), "visitors": row.c} for row in daily_visitors]
    
    # Daily page views
    from sqlalchemy import text
    daily_page_views = await db.execute(text("SELECT date_trunc('day', created_at) as d, count(*) as c FROM page_views WHERE created_at >= :start GROUP BY date_trunc('day', created_at) ORDER BY date_trunc('day', created_at)"), {"start": start_date})
    daily_page_views_data = [{"date": str(row.d.date()), "page_views": row.c} for row in daily_page_views]
    
    # Top pages
    top_pages = await db.execute(
        select(PageView.path, func.count(PageView.id).label('views'))
        .where(PageView.created_at >= start_date)
        .group_by(PageView.path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    top_pages_data = [{"path": row.path, "views": row.views} for row in top_pages]
    
    # Referrers
    referrers = await db.execute(
        select(PageView.referrer, func.count(PageView.id).label('count'))
        .where(PageView.created_at >= start_date)
        .where(PageView.referrer.isnot(None))
        .where(PageView.referrer != '')
        .group_by(PageView.referrer)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    referrers_data = [{"referrer": row.referrer, "count": row.count} for row in referrers]
    
    # Device types
    devices = await db.execute(
        select(Visitor.device_type, func.count(Visitor.id).label('count'))
        .where(Visitor.first_seen_at >= start_date)
        .where(Visitor.device_type.isnot(None))
        .group_by(Visitor.device_type)
        .order_by(func.count(Visitor.id).desc())
    )
    devices_data = [{"device": row.device_type, "count": row.count} for row in devices]
    
    # Browsers
    browsers = await db.execute(
        select(Visitor.browser, func.count(Visitor.id).label('count'))
        .where(Visitor.first_seen_at >= start_date)
        .where(Visitor.browser.isnot(None))
        .group_by(Visitor.browser)
        .order_by(func.count(Visitor.id).desc())
        .limit(8)
    )
    browsers_data = [{"browser": row.browser, "count": row.count} for row in browsers]
    
    # Countries
    countries = await db.execute(
        select(Visitor.country, func.count(Visitor.id).label('count'))
        .where(Visitor.first_seen_at >= start_date)
        .where(Visitor.country.isnot(None))
        .group_by(Visitor.country)
        .order_by(func.count(Visitor.id).desc())
        .limit(10)
    )
    countries_data = [{"country": row.country, "count": row.count} for row in countries]
    
    # Events by type
    events = await db.execute(
        select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id).label('count'))
        .where(AnalyticsEvent.created_at >= start_date)
        .group_by(AnalyticsEvent.event_type)
        .order_by(func.count(AnalyticsEvent.id).desc())
    )
    events_data = [{"event_type": row.event_type, "count": row.count} for row in events]
    
    # Section usage
    sections = await db.execute(
        select(UsageEvent.section, func.count(UsageEvent.id).label('count'))
        .where(UsageEvent.created_at >= start_date)
        .group_by(UsageEvent.section)
        .order_by(func.count(UsageEvent.id).desc())
    )
    sections_data = [{"section": row.section, "count": row.count} for row in sections]
    
    # Subscribers growth
    from sqlalchemy import text
    daily_subscribers = await db.execute(text("SELECT date_trunc('day', created_at) as d, count(*) as c FROM subscribers WHERE created_at >= :start GROUP BY date_trunc('day', created_at) ORDER BY date_trunc('day', created_at)"), {"start": start_date})
    daily_subscribers_data = [{"date": str(row.d.date()), "subscribers": row.c} for row in daily_subscribers]
    
    return WebsiteStatsResponse(
        period_days=days,
        total_visitors=total_visitors_count,
        total_page_views=total_page_views_count,
        total_subscribers=total_subscribers_count,
        total_users=total_users_count,
        daily_visitors=daily_visitors_data,
        daily_page_views=daily_page_views_data,
        daily_subscribers=daily_subscribers_data,
        top_pages=top_pages_data,
        referrers=referrers_data,
        devices=devices_data,
        browsers=browsers_data,
        countries=countries_data,
        events_by_type=events_data,
        section_usage=sections_data,
    )


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(db: AsyncSession = Depends(get_db)):
    """Get quick overview stats."""
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    
    today_visitors = await db.execute(select(func.count(Visitor.id)).where(Visitor.first_seen_at >= today_start))
    today_visitors_count = today_visitors.scalar() or 0
    
    today_pageviews = await db.execute(select(func.count(PageView.id)).where(PageView.created_at >= today_start))
    today_pageviews_count = today_pageviews.scalar() or 0
    
    yesterday_visitors = await db.execute(select(func.count(Visitor.id)).where(and_(Visitor.first_seen_at >= yesterday_start, Visitor.first_seen_at < today_start)))
    yesterday_visitors_count = yesterday_visitors.scalar() or 0
    
    yesterday_pageviews = await db.execute(select(func.count(PageView.id)).where(and_(PageView.created_at >= yesterday_start, PageView.created_at < today_start)))
    yesterday_pageviews_count = yesterday_pageviews.scalar() or 0
    
    active_sessions = await db.execute(select(func.count(func.distinct(PageView.session_id))).where(PageView.created_at >= now - timedelta(minutes=30)))
    active_sessions_count = active_sessions.scalar() or 0
    
    return AnalyticsOverviewResponse(
        today_visitors=today_visitors_count,
        today_page_views=today_pageviews_count,
        yesterday_visitors=yesterday_visitors_count,
        yesterday_page_views=yesterday_pageviews_count,
        active_sessions=active_sessions_count,
    )


@router.get("/analytics/subscribers/stats", response_model=SubscriberStatsResponse)
async def get_subscriber_stats(db: AsyncSession = Depends(get_db)):
    """Get subscriber statistics."""
    total = await db.execute(select(func.count(Subscriber.id)))
    active = await db.execute(select(func.count(Subscriber.id)).where(Subscriber.status == SubscriberStatus.ACTIVE.value))
    unsubscribed = await db.execute(select(func.count(Subscriber.id)).where(Subscriber.status == SubscriberStatus.UNSUBSCRIBED.value))
    bounced = await db.execute(select(func.count(Subscriber.id)).where(Subscriber.status == SubscriberStatus.BOUNCED.value))
    
    return SubscriberStatsResponse(
        total=total.scalar() or 0,
        active=active.scalar() or 0,
        unsubscribed=unsubscribed.scalar() or 0,
        bounced=bounced.scalar() or 0,
    )
