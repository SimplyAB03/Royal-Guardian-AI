from __future__ import annotations
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from royal_guardian.db.models import Agent, Device, Membership, Subscription
from royal_guardian.services.billing import entitlements


def tenant_plan(db: Session, tenant_id: str) -> str:
    sub=db.scalar(select(Subscription).where(Subscription.tenant_id==tenant_id).order_by(Subscription.updated_at.desc()))
    if sub and sub.status in {"active","trialing"}: return sub.plan
    return "free"


def require_capacity(db: Session, tenant_id: str, resource: str) -> None:
    limits=entitlements(tenant_plan(db,tenant_id))
    mapping={
        "agents": (Agent, "max_agents"),
        "devices": (Device, "max_devices"),
        "users": (Membership, "max_users"),
    }
    model,key=mapping[resource]
    count=db.scalar(select(func.count()).select_from(model).where(model.tenant_id==tenant_id)) or 0
    limit=int(limits.get(key,0))
    if count >= limit:
        raise PermissionError(f"Plan limit reached for {resource}: {count}/{limit}")
