from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from royal_guardian.core.config import settings
from royal_guardian.core.security import Principal, hash_password, hash_token, random_token, verify_password
from royal_guardian.db.models import Membership, Role, Session as AuthSession, Tenant, User
from royal_guardian.services.audit import record_audit


def _slugify(value: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return base or "workspace"


def register(db: Session, *, email: str, password: str, display_name: str, organization_name: str | None = None,
             is_business: bool = False) -> tuple[User, Tenant]:
    email = email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ValueError("An account with that email already exists")
    user = User(email=email, display_name=display_name.strip() or email.split("@")[0], password_hash=hash_password(password))
    db.add(user)
    db.flush()
    tenant_name = (organization_name or f"{user.display_name}'s Workspace").strip()
    slug_base = _slugify(tenant_name)
    slug = slug_base
    counter = 2
    while db.scalar(select(Tenant).where(Tenant.slug == slug)):
        slug = f"{slug_base}-{counter}"
        counter += 1
    tenant = Tenant(name=tenant_name, slug=slug, is_business=is_business)
    db.add(tenant)
    db.flush()
    db.add(Membership(tenant_id=tenant.id, user_id=user.id, role=Role.OWNER))
    record_audit(db, tenant_id=tenant.id, actor_type="user", actor_id=user.id, action="account.registered", target_type="tenant", target_id=tenant.id)
    db.commit()
    return user, tenant


def authenticate(db: Session, *, email: str, password: str) -> tuple[User, Membership] | None:
    user = db.scalar(select(User).where(User.email == email.strip().lower(), User.active.is_(True)))
    if not user or not verify_password(password, user.password_hash):
        return None
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id))
    if not membership:
        return None
    return user, membership


def create_session(db: Session, user: User, membership: Membership) -> str:
    raw = random_token(32)
    now = datetime.now(timezone.utc)
    auth_session = AuthSession(
        id=random_token(18),
        user_id=user.id,
        tenant_id=membership.tenant_id,
        token_hash=hash_token(raw),
        expires_at=now + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(auth_session)
    record_audit(db, tenant_id=membership.tenant_id, actor_type="user", actor_id=user.id, action="session.created")
    db.commit()
    return raw


def resolve_session(db: Session, raw_token: str) -> Principal | None:
    now = datetime.now(timezone.utc)
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token), AuthSession.expires_at > now))
    if not row:
        return None
    membership = db.scalar(select(Membership).where(Membership.user_id == row.user_id, Membership.tenant_id == row.tenant_id))
    if not membership:
        return None
    return Principal(user_id=row.user_id, tenant_id=row.tenant_id, role=membership.role.value)


def revoke_session(db: Session, raw_token: str) -> None:
    row=db.scalar(select(AuthSession).where(AuthSession.token_hash==hash_token(raw_token)))
    if row:
        db.delete(row); db.commit()
