"""Work group API endpoints: teams of users within a tenant."""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.models.work_group import WorkGroup, WorkGroupMember, WorkGroupRole
from backend.app.schemas import (
    UserResponse,
    WorkGroupCreate,
    WorkGroupDetailResponse,
    WorkGroupMemberAdd,
    WorkGroupMemberResponse,
    WorkGroupResponse,
    WorkGroupUpdate,
)
from backend.database import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "work-group"


async def _unique_slug(db: AsyncSession, tenant_id, name: str, exclude_id=None) -> str:
    base = _slugify(name)
    for attempt in range(100):
        slug = base if attempt == 0 else f"{base}-{uuid.uuid4().hex[:8]}"
        query = select(WorkGroup.id).where(
            WorkGroup.tenant_id == tenant_id, WorkGroup.slug == slug
        )
        if exclude_id is not None:
            query = query.where(WorkGroup.id != exclude_id)
        if (await db.execute(query)).scalar_one_or_none() is None:
            return slug
    raise HTTPException(status_code=503, detail="Unable to allocate a unique slug")


async def _member_count(db: AsyncSession, work_group_id) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(WorkGroupMember)
        .where(WorkGroupMember.work_group_id == work_group_id)
    )
    return int(result.scalar_one())


async def _load_scoped(db: AsyncSession, work_group_id, user: User) -> WorkGroup:
    """Fetch a work group and enforce that it belongs to the caller's tenant."""
    result = await db.execute(select(WorkGroup).where(WorkGroup.id == work_group_id))
    group = result.scalar_one_or_none()
    if not group or group.tenant_id != user.tenant_id:
        # Same response for both cases so IDs can't be probed across tenants.
        raise HTTPException(status_code=404, detail="Work group not found")
    return group


def _serialize(group: WorkGroup, member_count: int) -> WorkGroupResponse:
    return WorkGroupResponse(
        id=group.id,
        tenant_id=group.tenant_id,
        name=group.name,
        slug=group.slug,
        description=group.description,
        is_active=group.is_active,
        member_count=member_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.get("", response_model=list[WorkGroupResponse])
async def list_work_groups(
    include_inactive: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(WorkGroup).where(WorkGroup.tenant_id == user.tenant_id)
    if not include_inactive:
        query = query.where(WorkGroup.is_active.is_(True))
    query = query.order_by(WorkGroup.name)

    groups = (await db.execute(query)).scalars().all()
    return [_serialize(group, await _member_count(db, group.id)) for group in groups]


@router.post("", response_model=WorkGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_work_group(
    body: WorkGroupCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    slug = await _unique_slug(db, user.tenant_id, body.slug or body.name)
    group = WorkGroup(
        tenant_id=user.tenant_id,
        name=body.name,
        slug=slug,
        description=body.description.strip() if body.description else None,
        is_active=body.is_active,
    )
    db.add(group)
    await db.flush()

    # The creator becomes the owner so a group is never left unmanaged.
    db.add(
        WorkGroupMember(
            work_group_id=group.id,
            user_id=user.id,
            role=WorkGroupRole.OWNER.value,
        )
    )
    await db.commit()
    await db.refresh(group)
    return _serialize(group, 1)


@router.get("/{group_id}", response_model=WorkGroupDetailResponse)
async def get_work_group(
    group_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _load_scoped(db, group_id, user)

    members = (
        (
            await db.execute(
                select(WorkGroupMember)
                .options(selectinload(WorkGroupMember.user))
                .where(WorkGroupMember.work_group_id == group.id)
                .order_by(WorkGroupMember.joined_at)
            )
        )
        .scalars()
        .all()
    )

    return WorkGroupDetailResponse(
        **_serialize(group, len(members)).model_dump(),
        members=[
            WorkGroupMemberResponse(
                id=member.id,
                work_group_id=member.work_group_id,
                user_id=member.user_id,
                role=WorkGroupRole(member.role),
                joined_at=member.joined_at,
                user_email=member.user.email if member.user else None,
                user_full_name=member.user.full_name if member.user else None,
            )
            for member in members
        ],
    )


@router.patch("/{group_id}", response_model=WorkGroupResponse)
async def update_work_group(
    group_id: str,
    body: WorkGroupUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _load_scoped(db, group_id, user)

    if body.name is not None:
        group.name = body.name.strip()
        # Keep the slug in step with the name unless one was set explicitly.
        group.slug = await _unique_slug(db, user.tenant_id, body.name, exclude_id=group.id)
    if body.description is not None:
        group.description = body.description.strip() or None
    if body.is_active is not None:
        group.is_active = body.is_active

    await db.commit()
    await db.refresh(group)
    return _serialize(group, await _member_count(db, group.id))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_group(
    group_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _load_scoped(db, group_id, user)
    await db.delete(group)
    await db.commit()


@router.get("/{group_id}/members", response_model=list[WorkGroupMemberResponse])
async def list_members(
    group_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _load_scoped(db, group_id, user)
    members = (
        (
            await db.execute(
                select(WorkGroupMember)
                .options(selectinload(WorkGroupMember.user))
                .where(WorkGroupMember.work_group_id == group.id)
                .order_by(WorkGroupMember.joined_at)
            )
        )
        .scalars()
        .all()
    )
    return [
        WorkGroupMemberResponse(
            id=member.id,
            work_group_id=member.work_group_id,
            user_id=member.user_id,
            role=WorkGroupRole(member.role),
            joined_at=member.joined_at,
            user_email=member.user.email if member.user else None,
            user_full_name=member.user.full_name if member.user else None,
        )
        for member in members
    ]


@router.post(
    "/{group_id}/members",
    response_model=WorkGroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    group_id: str,
    body: WorkGroupMemberAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _load_scoped(db, group_id, user)

    # Members must already exist in this tenant — never another tenant's user.
    member_user = await db.get(User, body.user_id)
    if not member_user or member_user.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="User not found in this workspace")

    existing = await db.execute(
        select(WorkGroupMember).where(
            WorkGroupMember.work_group_id == group.id,
            WorkGroupMember.user_id == body.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    member = WorkGroupMember(
        work_group_id=group.id,
        user_id=body.user_id,
        role=body.role.value,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return WorkGroupMemberResponse(
        id=member.id,
        work_group_id=member.work_group_id,
        user_id=member.user_id,
        role=WorkGroupRole(member.role),
        joined_at=member.joined_at,
        user_email=member_user.email,
        user_full_name=member_user.full_name,
    )


@router.delete("/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    member_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _load_scoped(db, group_id, user)

    member = await db.get(WorkGroupMember, member_id)
    if not member or member.work_group_id != group.id:
        raise HTTPException(status_code=404, detail="Member not found")

    # A group must always retain at least one owner.
    if member.role == WorkGroupRole.OWNER.value:
        owners = (
            await db.execute(
                select(func.count())
                .select_from(WorkGroupMember)
                .where(
                    WorkGroupMember.work_group_id == group.id,
                    WorkGroupMember.role == WorkGroupRole.OWNER.value,
                )
            )
        ).scalar_one()
        if owners <= 1:
            raise HTTPException(
                status_code=409,
                detail="A work group must keep at least one owner",
            )

    await db.delete(member)
    await db.commit()


@router.get("/{group_id}/candidates", response_model=list[UserResponse])
async def list_candidates(
    group_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Users in the tenant who are not yet members of this group."""
    group = await _load_scoped(db, group_id, user)

    result = await db.execute(
        select(User)
        .where(
            User.tenant_id == user.tenant_id,
            User.is_active.is_(True),
            User.id.not_in(
                select(WorkGroupMember.user_id).where(
                    WorkGroupMember.work_group_id == group.id
                )
            ),
        )
        .order_by(User.email)
    )
    return [UserResponse.model_validate(candidate) for candidate in result.scalars().all()]