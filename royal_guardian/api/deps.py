from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from royal_guardian.core.security import Principal, hash_token
from royal_guardian.db.base import SessionLocal
from royal_guardian.db.models import Device
from royal_guardian.services.auth import resolve_session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_principal(rg_session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> Principal:
    if not rg_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    principal = resolve_session(db, rg_session)
    if not principal:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return principal


def require_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.role not in {"admin", "owner", "platform_admin"}:
        raise HTTPException(status_code=403, detail="Administrator permission required")
    return principal


def get_device(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Device:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Device authentication required")
    raw = authorization.split(" ", 1)[1].strip()
    device = db.query(Device).filter(Device.auth_token_hash == hash_token(raw)).first()
    if not device or device.status.value == "revoked":
        raise HTTPException(status_code=401, detail="Invalid device credential")
    return device
