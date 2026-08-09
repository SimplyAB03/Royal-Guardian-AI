from sqlalchemy import select

from royal_guardian.db.base import SessionLocal, init_db
from royal_guardian.db.models import Agent
from royal_guardian.services.auth import register


def test_tenants_are_distinct():
    init_db()
    db = SessionLocal()
    try:
        u1, t1 = register(db, email="one@example.com", password="first-password", display_name="One")
        u2, t2 = register(db, email="two@example.com", password="second-password", display_name="Two")
        assert t1.id != t2.id
        db.add(Agent(tenant_id=t1.id, owner_id=u1.id, name="Private Agent"))
        db.commit()
        visible_to_t2 = db.scalars(select(Agent).where(Agent.tenant_id == t2.id)).all()
        assert visible_to_t2 == []
    finally:
        db.close()
