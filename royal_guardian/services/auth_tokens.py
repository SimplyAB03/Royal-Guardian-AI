from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from royal_guardian.core.security import hash_token, random_token
from royal_guardian.db.models import AuthToken, AuthTokenType


def create_auth_token(db: Session, token_type: AuthTokenType, *, user_id: str = "", tenant_id: str = "", email: str = "", role: str = "member", ttl_minutes: int = 30) -> str:
    raw = random_token(32)
    db.add(AuthToken(token_hash=hash_token(raw), token_type=token_type, user_id=user_id, tenant_id=tenant_id, email=email.lower().strip(), role=role, expires_at=datetime.now(timezone.utc)+timedelta(minutes=ttl_minutes)))
    db.flush()
    return raw


def consume_auth_token(db: Session, raw: str, token_type: AuthTokenType) -> AuthToken | None:
    now=datetime.now(timezone.utc)
    row=db.scalar(select(AuthToken).where(AuthToken.token_hash==hash_token(raw), AuthToken.token_type==token_type, AuthToken.used_at.is_(None), AuthToken.expires_at>now))
    if row:
        row.used_at=now
        db.flush()
    return row
