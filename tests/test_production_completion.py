from fastapi.testclient import TestClient
from sqlalchemy import select
from royal_guardian.api.main import app
from royal_guardian.db.base import SessionLocal
from royal_guardian.db.models import Subscription, Workflow, WorkflowRunStatus
from royal_guardian.services.mfa import totp
from royal_guardian.services.secrets import decrypt_json
from royal_guardian.services.workflows import queue_workflow


def _register(client,email="prod@example.com",business=False):
    r=client.post("/api/auth/register",json={"email":email,"password":"very-secure-password","display_name":"Prod User","organization_name":"Prod Co","is_business":business})
    assert r.status_code==201,r.text
    return r.json()


def test_verification_reset_and_mfa_flow():
    with TestClient(app) as client:
        data=_register(client,"secure@example.com")
        token=data["development_email_verification_token"]
        assert client.post("/api/auth/verify-email",json={"token":token}).status_code==200
        setup=client.post("/api/auth/mfa/setup").json()
        code=totp(setup["secret"])
        assert client.post("/api/auth/mfa/enable",json={"code":code}).status_code==200
        client.post("/api/auth/logout")
        denied=client.post("/api/auth/login",json={"email":"secure@example.com","password":"very-secure-password"})
        assert denied.status_code==401
        ok=client.post("/api/auth/login",json={"email":"secure@example.com","password":"very-secure-password","mfa_code":totp(setup["secret"])})
        assert ok.status_code==200
        reset=client.post("/api/auth/password-reset/request",json={"email":"secure@example.com"}).json()
        assert client.post("/api/auth/password-reset/confirm",json={"token":reset["development_password_reset_token"],"new_password":"another-secure-password"}).status_code==200


def test_entitlement_blocks_second_free_agent():
    with TestClient(app) as client:
        _register(client,"limit@example.com")
        assert client.post("/api/agents",json={"name":"One"}).status_code==201
        r=client.post("/api/agents",json={"name":"Two"})
        assert r.status_code==402


def test_business_invitation_with_paid_entitlement():
    with TestClient(app) as client:
        data=_register(client,"owner2@example.com",True)
        tenant_id=data["tenant"]["id"]
        with SessionLocal() as db:
            db.add(Subscription(tenant_id=tenant_id,plan="business",status="active")); db.commit()
        invite=client.post("/api/organization/invitations",json={"email":"member@example.com","role":"member"})
        assert invite.status_code==201,invite.text
        token=invite.json()["development_invitation_token"]
        other=TestClient(app)
        with other:
            accepted=other.post("/api/organization/invitations/accept",json={"token":token,"display_name":"Member","password":"member-secure-password"})
            assert accepted.status_code==200,accepted.text
            assert accepted.json()["role"]=="member"


def test_workflow_queue_is_persistent():
    with TestClient(app) as client:
        _register(client,"workflow@example.com")
        agent=client.post("/api/agents",json={"name":"Worker"}).json()
        wf=client.post("/api/workflows",json={"name":"Daily","agent_id":agent["id"],"trigger_type":"manual","definition":{"prompt":"Summarize work"}})
        assert wf.status_code==201
        queued=client.post(f"/api/workflows/{wf.json()['id']}/run",json={"input":{"message":"hello"}})
        assert queued.status_code==202
        runs=client.get("/api/workflow-runs").json()
        assert any(r["id"]==queued.json()["run_id"] and r["status"]=="queued" for r in runs)


def test_security_headers_present():
    with TestClient(app) as client:
        r=client.get("/health")
        assert r.headers["x-content-type-options"]=="nosniff"
        assert r.headers["x-frame-options"]=="DENY"
