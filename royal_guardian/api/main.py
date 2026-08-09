from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from royal_guardian import __version__
from royal_guardian.api.deps import get_db, get_device, get_principal, require_admin
from royal_guardian.api.schemas import AgentCreate, AgentRunRequest, CommandCreate, CommandResult, DeviceEnroll, DeviceHeartbeat, EnrollmentCreate, LoginRequest, RegisterRequest, ApprovalDecision, MemoryCreate, KnowledgeCreate, WorkflowCreate, CheckoutCreate, LoginMFARequest, MFASetupConfirm, PasswordResetRequest, PasswordResetConfirm, VerifyEmailRequest, InviteCreate, InviteAccept, WorkflowRunCreate, WorkflowScheduleUpdate
from royal_guardian.core.config import ROOT, settings
from royal_guardian.core.security import Principal, hash_token, random_token, hash_password
from royal_guardian.db.base import init_db
from royal_guardian.db.models import Agent, AgentRun, AuditEvent, CommandStatus, Device, DeviceCommand, DeviceStatus, EnrollmentToken, Membership, Tenant, User, Approval, ApprovalStatus, MemoryItem, KnowledgeDocument, IntegrationConnection, Subscription, Workflow, AuthTokenType, Role, WorkflowRun, WorkflowRunStatus
from royal_guardian.integrations import INTEGRATIONS
from royal_guardian.services.audit import record_audit
from royal_guardian.services.auth import authenticate, create_session, register
from royal_guardian.services.ai import AIProviderError
from royal_guardian.services.runtime import run_agent_runtime
from royal_guardian.services.oauth import PROVIDERS as OAUTH_PROVIDERS, authorization_url, exchange_code, parse_state
from royal_guardian.services.secrets import encrypt_json, decrypt_json
from royal_guardian.services.billing import create_checkout, create_portal, entitlements, verify_webhook, plan_from_price
from royal_guardian.services.auth_tokens import create_auth_token, consume_auth_token
from royal_guardian.services.mfa import generate_secret, provisioning_uri, verify_totp
from royal_guardian.services.approval_execution import execute_approved
from royal_guardian.services.entitlements import require_capacity
from royal_guardian.core.http_security import SECURITY_HEADERS, origin_allowed
from royal_guardian.services.email import send_email, configured as email_configured, EmailDeliveryError

@asynccontextmanager
async def lifespan(app: FastAPI):
    (ROOT / "data").mkdir(exist_ok=True)
    init_db()
    if settings.production and settings.session_secret == "change-me-in-production":
        raise RuntimeError("RG_SESSION_SECRET must be changed in production")
    if settings.production and (settings.encryption_secret == "change-me-in-production" or settings.encryption_secret == settings.session_secret):
        raise RuntimeError("RG_ENCRYPTION_SECRET must be a separate production secret")
    yield


app = FastAPI(title="Royal Guardian API", version=__version__, lifespan=lifespan)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if not origin_allowed(request):
        return Response(content='{"detail":"Invalid request origin"}', status_code=403, media_type="application/json")
    response=await call_next(request)
    for k,v in SECURITY_HEADERS.items(): response.headers.setdefault(k,v)
    if settings.production: response.headers.setdefault("Strict-Transport-Security","max-age=31536000; includeSubDomains")
    return response
WEB_DIR = ROOT / "web"
STATIC_DIR = WEB_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/app")
def web_app():
    return FileResponse(WEB_DIR / "app.html")


@app.get("/health")
def health():
    return {"ok": True, "service": "royal-guardian", "version": __version__, "timestamp": int(time.time())}


@app.post("/api/auth/register", status_code=201)
def register_user(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if not settings.allow_registration:
        raise HTTPException(status_code=403, detail="Registration disabled")
    try:
        user, tenant = register(db, email=str(payload.email), password=payload.password, display_name=payload.display_name,
                                organization_name=payload.organization_name, is_business=payload.is_business)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.tenant_id == tenant.id))
    verify_token=create_auth_token(db,AuthTokenType.EMAIL_VERIFY,user_id=user.id,tenant_id=tenant.id,email=user.email,ttl_minutes=1440)
    db.commit()
    if email_configured():
        try: send_email(user.email,"Verify your Royal Guardian account",f"Verify your account: {settings.public_base_url.rstrip('/')}/app?verify={verify_token}")
        except EmailDeliveryError: pass
    token = create_session(db, user, membership)
    response.set_cookie("rg_session", token, httponly=True, samesite="lax", secure=settings.production, max_age=settings.session_ttl_seconds)
    result={"user": {"id": user.id, "email": user.email, "display_name": user.display_name, "email_verified":user.email_verified}, "tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}}
    if not settings.production: result["development_email_verification_token"]=verify_token
    return result


@app.post("/api/auth/login")
def login(payload: LoginMFARequest, response: Response, db: Session = Depends(get_db)):
    result = authenticate(db, email=str(payload.email), password=payload.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user, membership = result
    if user.mfa_enabled:
        secret=decrypt_json(user.mfa_secret_encrypted).get("secret","")
        if not payload.mfa_code or not secret or not verify_totp(secret,payload.mfa_code):
            raise HTTPException(status_code=401,detail="Valid MFA code required")
    token = create_session(db, user, membership)
    response.set_cookie("rg_session", token, httponly=True, samesite="lax", secure=settings.production, max_age=settings.session_ttl_seconds)
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("rg_session")
    return {"ok": True}


@app.get("/api/me")
def me(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    user = db.get(User, principal.user_id)
    tenant = db.get(Tenant, principal.tenant_id)
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "email_verified":user.email_verified, "mfa_enabled":user.mfa_enabled, "tenant": {"id": tenant.id, "name": tenant.name, "is_business": tenant.is_business}, "role": principal.role}


@app.get("/api/agents")
def list_agents(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    rows = db.scalars(select(Agent).where(Agent.tenant_id == principal.tenant_id).order_by(Agent.created_at.desc())).all()
    return [{"id": a.id, "name": a.name, "description": a.description, "status": a.status.value, "tools": a.tools, "model_provider": a.model_provider, "model_name": a.model_name, "version": a.version} for a in rows]


@app.post("/api/agents", status_code=201)
def create_agent(payload: AgentCreate, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    try: require_capacity(db,principal.tenant_id,"agents")
    except PermissionError as exc: raise HTTPException(status_code=402,detail=str(exc)) from exc
    agent = Agent(tenant_id=principal.tenant_id, owner_id=principal.user_id, **payload.model_dump())
    db.add(agent)
    db.flush()
    record_audit(db, tenant_id=principal.tenant_id, actor_type="user", actor_id=principal.user_id, action="agent.created", target_type="agent", target_id=agent.id)
    db.commit()
    return {"id": agent.id, "name": agent.name, "status": agent.status.value}


@app.post("/api/agents/{agent_id}/run")
def run_agent(agent_id: str, payload: AgentRunRequest, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    agent = db.scalar(select(Agent).where(Agent.id == agent_id, Agent.tenant_id == principal.tenant_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    run = AgentRun(tenant_id=principal.tenant_id, agent_id=agent.id, user_id=principal.user_id, input_text=payload.message, provider=agent.model_provider, model=agent.model_name)
    db.add(run)
    db.flush()
    system = agent.role_prompt or f"You are {agent.name}. {agent.description}"
    if agent.objectives:
        system += "\nObjectives:\n- " + "\n- ".join(str(x) for x in agent.objectives)
    try:
        result = run_agent_runtime(db, agent=agent, run=run, user_id=principal.user_id, message=payload.message, max_tokens=payload.max_tokens)
        run.output_text = result["text"]
        run.usage = result["usage"]
        run.status = "succeeded"
        run.completed_at = datetime.now(timezone.utc)
        record_audit(db, tenant_id=principal.tenant_id, actor_type="user", actor_id=principal.user_id, action="agent.run.succeeded", target_type="agent_run", target_id=run.id, metadata={"agent_id": agent.id, "provider": result["provider"], "model": result["model"]})
        db.commit()
        return {"run_id": run.id, **result}
    except AIProviderError as exc:
        run.status = "blocked"
        run.error = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/agents/{agent_id}/runs")
def list_agent_runs(agent_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    agent = db.scalar(select(Agent).where(Agent.id == agent_id, Agent.tenant_id == principal.tenant_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    rows = db.scalars(select(AgentRun).where(AgentRun.agent_id == agent_id, AgentRun.tenant_id == principal.tenant_id).order_by(AgentRun.created_at.desc()).limit(100)).all()
    return [{"id": r.id, "input": r.input_text, "output": r.output_text, "status": r.status, "provider": r.provider, "model": r.model, "usage": r.usage, "error": r.error, "created_at": r.created_at.isoformat()} for r in rows]


@app.get("/api/integrations")
def integrations(principal: Principal = Depends(get_principal)):
    return [{"id": i.id, "name": i.name, "status": i.status.value, "required_environment": list(i.required_environment)} for i in INTEGRATIONS]


@app.get("/api/audit")
def audit(principal: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditEvent).where(AuditEvent.tenant_id == principal.tenant_id).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [{"id": e.id, "action": e.action, "actor_type": e.actor_type, "actor_id": e.actor_id, "target_type": e.target_type, "target_id": e.target_id, "metadata": e.metadata_json, "created_at": e.created_at.isoformat()} for e in rows]


@app.post("/api/devices/enrollment-tokens", status_code=201)
def create_enrollment(payload: EnrollmentCreate, principal: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    raw = random_token(24)
    row = EnrollmentToken(tenant_id=principal.tenant_id, token_hash=hash_token(raw), expires_at=datetime.now(timezone.utc) + timedelta(minutes=payload.ttl_minutes), created_by=principal.user_id)
    db.add(row)
    record_audit(db, tenant_id=principal.tenant_id, actor_type="user", actor_id=principal.user_id, action="device.enrollment_token.created", target_type="enrollment_token", target_id=row.id)
    db.commit()
    return {"token": raw, "expires_at": row.expires_at.isoformat()}


@app.post("/api/devices/enroll", status_code=201)
def enroll_device(payload: DeviceEnroll, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    token_row = db.scalar(select(EnrollmentToken).where(EnrollmentToken.token_hash == hash_token(payload.enrollment_token), EnrollmentToken.used_at.is_(None), EnrollmentToken.expires_at > now))
    if not token_row:
        raise HTTPException(status_code=400, detail="Invalid, expired, or already-used enrollment token")
    try: require_capacity(db,token_row.tenant_id,"devices")
    except PermissionError as exc: raise HTTPException(status_code=402,detail=str(exc)) from exc
    existing = db.scalar(select(Device).where(Device.tenant_id == token_row.tenant_id, Device.fingerprint == payload.fingerprint))
    if existing and existing.status != DeviceStatus.REVOKED:
        raise HTTPException(status_code=409, detail="Device is already enrolled")
    credential = random_token(32)
    device = Device(tenant_id=token_row.tenant_id, name=payload.name, platform=payload.platform, fingerprint=payload.fingerprint, auth_token_hash=hash_token(credential), status=DeviceStatus.ONLINE, last_seen_at=now)
    db.add(device)
    token_row.used_at = now
    record_audit(db, tenant_id=token_row.tenant_id, actor_type="device", actor_id=device.id, action="device.enrolled", target_type="device", target_id=device.id)
    db.commit()
    return {"device_id": device.id, "device_token": credential}


@app.post("/api/device/heartbeat")
def device_heartbeat(payload: DeviceHeartbeat, device: Device = Depends(get_device), db: Session = Depends(get_db)):
    device.status = DeviceStatus.ONLINE
    device.last_seen_at = datetime.now(timezone.utc)
    device.diagnostics = payload.diagnostics
    db.add(device)
    db.commit()
    return {"ok": True, "device_id": device.id}


@app.get("/api/devices")
def list_devices(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    rows = db.scalars(select(Device).where(Device.tenant_id == principal.tenant_id).order_by(Device.created_at.desc())).all()
    return [{"id": d.id, "name": d.name, "platform": d.platform, "status": d.status.value, "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None, "diagnostics": d.diagnostics} for d in rows]


@app.post("/api/devices/{device_id}/commands", status_code=201)
def create_command(device_id: str, payload: CommandCreate, principal: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    device = db.scalar(select(Device).where(Device.id == device_id, Device.tenant_id == principal.tenant_id))
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    from endpoint.actions import ACTIONS
    action = ACTIONS.get(payload.action_id)
    if not action:
        raise HTTPException(status_code=400, detail="Unknown or non-allowlisted action")
    if action["risk"] == "prohibited":
        raise HTTPException(status_code=403, detail="Action is prohibited")
    if action["approval_required"] and not payload.approved:
        raise HTTPException(status_code=409, detail="Explicit approval required")
    cmd = DeviceCommand(tenant_id=principal.tenant_id, device_id=device.id, action_id=payload.action_id, parameters=payload.parameters, risk=action["risk"], created_by=principal.user_id)
    db.add(cmd)
    db.flush()
    record_audit(db, tenant_id=principal.tenant_id, actor_type="user", actor_id=principal.user_id, action="device.command.queued", target_type="device_command", target_id=cmd.id, metadata={"device_id": device.id, "action_id": payload.action_id})
    db.commit()
    return {"id": cmd.id, "status": cmd.status.value}


@app.get("/api/device/commands/next")
def next_command(device: Device = Depends(get_device), db: Session = Depends(get_db)):
    cmd = db.scalar(select(DeviceCommand).where(DeviceCommand.device_id == device.id, DeviceCommand.status == CommandStatus.QUEUED).order_by(DeviceCommand.created_at.asc()))
    if not cmd:
        return {"command": None}
    cmd.status = CommandStatus.RUNNING
    db.commit()
    return {"command": {"id": cmd.id, "action_id": cmd.action_id, "parameters": cmd.parameters, "risk": cmd.risk}}


@app.post("/api/device/commands/{command_id}/result")
def command_result(command_id: str, payload: CommandResult, device: Device = Depends(get_device), db: Session = Depends(get_db)):
    cmd = db.scalar(select(DeviceCommand).where(DeviceCommand.id == command_id, DeviceCommand.device_id == device.id, DeviceCommand.tenant_id == device.tenant_id))
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    cmd.status = CommandStatus.SUCCEEDED if payload.ok else CommandStatus.FAILED
    cmd.result = {"result": payload.result, "error": payload.error}
    cmd.completed_at = datetime.now(timezone.utc)
    record_audit(db, tenant_id=device.tenant_id, actor_type="device", actor_id=device.id, action="device.command.completed", target_type="device_command", target_id=cmd.id, metadata={"ok": payload.ok, "action_id": cmd.action_id})
    db.commit()
    return {"ok": True}

@app.get("/api/approvals")
def list_approvals(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    rows=db.scalars(select(Approval).where(Approval.tenant_id==principal.tenant_id).order_by(Approval.created_at.desc()).limit(200)).all()
    return [{"id":a.id,"agent_id":a.agent_id,"run_id":a.run_id,"tool_id":a.tool_id,"parameters":a.parameters,"risk":a.risk,"status":a.status.value,"reason":a.reason,"created_at":a.created_at.isoformat()} for a in rows]

@app.post("/api/approvals/{approval_id}/decision")
def decide_approval(approval_id:str, payload:ApprovalDecision, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    a=db.scalar(select(Approval).where(Approval.id==approval_id,Approval.tenant_id==principal.tenant_id))
    if not a: raise HTTPException(status_code=404,detail="Approval not found")
    if a.status != ApprovalStatus.PENDING: raise HTTPException(status_code=409,detail="Approval already decided")
    if a.risk in {"high","medium"} and principal.role not in {"owner","admin","platform_admin"}:
        raise HTTPException(status_code=403,detail="Administrator approval required")
    a.status=ApprovalStatus.APPROVED if payload.approve else ApprovalStatus.REJECTED
    a.approver_id=principal.user_id; a.reason=payload.reason; a.decided_at=datetime.now(timezone.utc)
    execution={"ok":False,"skipped":True}
    if payload.approve:
        try: execution=execute_approved(db,a,principal.user_id)
        except Exception as exc:
            a.status=ApprovalStatus.PENDING; a.approver_id=""; a.decided_at=None
            db.rollback(); raise HTTPException(status_code=502,detail=f"Approved action execution failed: {exc}") from exc
    record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="approval.approved" if payload.approve else "approval.rejected",target_type="approval",target_id=a.id,metadata={"execution":execution})
    db.commit(); return {"id":a.id,"status":a.status.value,"execution":execution}

@app.get("/api/memory")
def list_memory(agent_id:str="", principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    q=select(MemoryItem).where(MemoryItem.tenant_id==principal.tenant_id)
    if agent_id: q=q.where(MemoryItem.agent_id==agent_id)
    rows=db.scalars(q.order_by(MemoryItem.created_at.desc()).limit(200)).all()
    return [{"id":m.id,"agent_id":m.agent_id,"scope":m.scope,"key":m.key,"content":m.content,"created_at":m.created_at.isoformat()} for m in rows]

@app.post("/api/memory", status_code=201)
def create_memory(payload:MemoryCreate, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    if payload.scope=="organization" and principal.role not in {"owner","admin","platform_admin"}: raise HTTPException(status_code=403,detail="Administrator permission required")
    if payload.agent_id and not db.scalar(select(Agent).where(Agent.id==payload.agent_id,Agent.tenant_id==principal.tenant_id)): raise HTTPException(status_code=404,detail="Agent not found")
    m=MemoryItem(tenant_id=principal.tenant_id,owner_id=principal.user_id,**payload.model_dump()); db.add(m); db.flush()
    record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="memory.created",target_type="memory",target_id=m.id); db.commit()
    return {"id":m.id}

@app.delete("/api/memory/{memory_id}")
def delete_memory(memory_id:str, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    m=db.scalar(select(MemoryItem).where(MemoryItem.id==memory_id,MemoryItem.tenant_id==principal.tenant_id))
    if not m: raise HTTPException(status_code=404,detail="Memory not found")
    db.delete(m); record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="memory.deleted",target_type="memory",target_id=memory_id); db.commit(); return {"ok":True}

@app.get("/api/knowledge")
def list_knowledge(principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    rows=db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.tenant_id==principal.tenant_id).order_by(KnowledgeDocument.created_at.desc())).all()
    return [{"id":d.id,"agent_id":d.agent_id,"name":d.name,"mime_type":d.mime_type,"size_bytes":d.size_bytes,"created_at":d.created_at.isoformat()} for d in rows]

@app.post("/api/knowledge", status_code=201)
def create_knowledge(payload:KnowledgeCreate, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    if payload.agent_id and not db.scalar(select(Agent).where(Agent.id==payload.agent_id,Agent.tenant_id==principal.tenant_id)): raise HTTPException(status_code=404,detail="Agent not found")
    raw=payload.content.encode("utf-8")
    d=KnowledgeDocument(tenant_id=principal.tenant_id,owner_id=principal.user_id,agent_id=payload.agent_id,name=payload.name,mime_type=payload.mime_type,content_text=payload.content,size_bytes=len(raw)); db.add(d); db.flush()
    record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="knowledge.created",target_type="knowledge",target_id=d.id); db.commit(); return {"id":d.id,"size_bytes":d.size_bytes}

@app.delete("/api/knowledge/{doc_id}")
def delete_knowledge(doc_id:str, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    d=db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id==doc_id,KnowledgeDocument.tenant_id==principal.tenant_id))
    if not d: raise HTTPException(status_code=404,detail="Document not found")
    db.delete(d); record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="knowledge.deleted",target_type="knowledge",target_id=doc_id); db.commit(); return {"ok":True}

@app.get("/api/workflows")
def list_workflows(principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    rows=db.scalars(select(Workflow).where(Workflow.tenant_id==principal.tenant_id).order_by(Workflow.created_at.desc())).all()
    return [{"id":w.id,"agent_id":w.agent_id,"name":w.name,"trigger_type":w.trigger_type,"definition":w.definition,"enabled":w.enabled,"schedule_interval_seconds":w.schedule_interval_seconds,"next_run_at":w.next_run_at.isoformat() if w.next_run_at else None} for w in rows]

@app.post("/api/workflows",status_code=201)
def create_workflow(payload:WorkflowCreate, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    w=Workflow(tenant_id=principal.tenant_id,owner_id=principal.user_id,**payload.model_dump()); db.add(w); db.flush(); record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="workflow.created",target_type="workflow",target_id=w.id); db.commit(); return {"id":w.id}

@app.get("/api/oauth/{provider}/start")
def oauth_start(provider:str, principal:Principal=Depends(get_principal)):
    if provider not in OAUTH_PROVIDERS: raise HTTPException(status_code=404,detail="OAuth provider not supported")
    try: return {"authorization_url":authorization_url(provider,principal.user_id,principal.tenant_id)}
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc)) from exc

@app.get("/api/oauth/{provider}/callback")
def oauth_callback(provider:str, code:str, state:str, db:Session=Depends(get_db)):
    parsed=parse_state(state,provider)
    if not parsed: raise HTTPException(status_code=400,detail="Invalid or expired OAuth state")
    tenant_id,user_id=parsed
    try: tokens=exchange_code(provider,code)
    except Exception as exc: raise HTTPException(status_code=502,detail=f"OAuth token exchange failed: {exc}") from exc
    existing=db.scalar(select(IntegrationConnection).where(IntegrationConnection.tenant_id==tenant_id,IntegrationConnection.user_id==user_id,IntegrationConnection.provider==provider))
    if not existing:
        existing=IntegrationConnection(tenant_id=tenant_id,user_id=user_id,provider=provider); db.add(existing)
    existing.encrypted_tokens=encrypt_json(tokens); existing.scopes=str(tokens.get("scope","")).split(); existing.status="connected"
    record_audit(db,tenant_id=tenant_id,actor_type="user",actor_id=user_id,action="integration.connected",target_type="integration",target_id=provider); db.commit()
    return RedirectResponse(url="/app#connections")

@app.get("/api/connections")
def list_connections(principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    rows=db.scalars(select(IntegrationConnection).where(IntegrationConnection.tenant_id==principal.tenant_id,IntegrationConnection.user_id==principal.user_id)).all()
    return [{"id":c.id,"provider":c.provider,"account_label":c.account_label,"scopes":c.scopes,"status":c.status} for c in rows]

@app.delete("/api/connections/{connection_id}")
def disconnect(connection_id:str, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    c=db.scalar(select(IntegrationConnection).where(IntegrationConnection.id==connection_id,IntegrationConnection.tenant_id==principal.tenant_id,IntegrationConnection.user_id==principal.user_id))
    if not c: raise HTTPException(status_code=404,detail="Connection not found")
    provider=c.provider; db.delete(c); record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="integration.disconnected",target_type="integration",target_id=provider); db.commit(); return {"ok":True}

@app.get("/api/billing")
def billing_status(principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    s=db.scalar(select(Subscription).where(Subscription.tenant_id==principal.tenant_id))
    plan=s.plan if s else "free"; return {"plan":plan,"status":s.status if s else "active","entitlements":entitlements(plan)}

@app.post("/api/billing/checkout")
def billing_checkout(payload:CheckoutCreate, principal:Principal=Depends(require_admin), db:Session=Depends(get_db)):
    u=db.get(User,principal.user_id); base=settings.public_base_url.rstrip("/")
    try: session=create_checkout(tenant_id=principal.tenant_id,user_email=u.email,plan=payload.plan,success_url=payload.success_url or f"{base}/app?billing=success",cancel_url=payload.cancel_url or f"{base}/app?billing=cancelled")
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc)) from exc
    return {"checkout_url":session.get("url"),"session_id":session.get("id")}

@app.post("/api/billing/portal")
def billing_portal(principal:Principal=Depends(require_admin), db:Session=Depends(get_db)):
    s=db.scalar(select(Subscription).where(Subscription.tenant_id==principal.tenant_id))
    if not s or not s.customer_id: raise HTTPException(status_code=409,detail="No Stripe customer is associated with this workspace")
    try: portal=create_portal(s.customer_id,settings.public_base_url.rstrip("/")+"/app")
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc)) from exc
    return {"url":portal.get("url")}

@app.post("/api/billing/webhook")
async def billing_webhook(request:Request, db:Session=Depends(get_db)):
    raw=await request.body(); sig=request.headers.get("stripe-signature","")
    if not verify_webhook(raw,sig): raise HTTPException(status_code=400,detail="Invalid Stripe signature")
    event=__import__('json').loads(raw); obj=event.get("data",{}).get("object",{}); typ=event.get("type","")
    metadata=obj.get("metadata") or {}; tenant_id=metadata.get("tenant_id","")
    if typ=="checkout.session.completed" and tenant_id:
        s=db.scalar(select(Subscription).where(Subscription.tenant_id==tenant_id)) or Subscription(tenant_id=tenant_id); db.add(s)
        s.customer_id=obj.get("customer") or s.customer_id; s.subscription_id=obj.get("subscription") or s.subscription_id; s.plan=metadata.get("plan",s.plan); s.status="active"; db.commit()
    elif typ in {"customer.subscription.created","customer.subscription.updated","customer.subscription.deleted"} and tenant_id:
        s=db.scalar(select(Subscription).where(Subscription.tenant_id==tenant_id)) or Subscription(tenant_id=tenant_id); db.add(s)
        items=(obj.get("items") or {}).get("data") or []; price_id=((items[0].get("price") or {}).get("id") if items else "")
        s.customer_id=obj.get("customer") or s.customer_id; s.subscription_id=obj.get("id") or s.subscription_id; s.plan=metadata.get("plan") or plan_from_price(price_id) or s.plan; s.status="canceled" if typ=="customer.subscription.deleted" else (obj.get("status") or s.status); db.commit()
    return {"received":True}

# --- Production-completion auth and organization APIs ---
@app.post("/api/auth/verify-email")
def verify_email(payload: VerifyEmailRequest, db:Session=Depends(get_db)):
    row=consume_auth_token(db,payload.token,AuthTokenType.EMAIL_VERIFY)
    if not row: raise HTTPException(status_code=400,detail="Invalid or expired verification token")
    user=db.get(User,row.user_id)
    if not user: raise HTTPException(status_code=404,detail="User not found")
    user.email_verified=True; db.commit(); return {"ok":True}

@app.post("/api/auth/password-reset/request")
def password_reset_request(payload:PasswordResetRequest, db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==str(payload.email).lower()))
    result={"ok":True}
    if user:
        membership=db.scalar(select(Membership).where(Membership.user_id==user.id))
        token=create_auth_token(db,AuthTokenType.PASSWORD_RESET,user_id=user.id,tenant_id=membership.tenant_id if membership else "",email=user.email,ttl_minutes=30)
        db.commit()
        if email_configured():
            try: send_email(user.email,"Reset your Royal Guardian password",f"Reset your password: {settings.public_base_url.rstrip('/')}/app?reset={token}")
            except EmailDeliveryError: pass
        if not settings.production: result["development_password_reset_token"]=token
    return result

@app.post("/api/auth/password-reset/confirm")
def password_reset_confirm(payload:PasswordResetConfirm, db:Session=Depends(get_db)):
    row=consume_auth_token(db,payload.token,AuthTokenType.PASSWORD_RESET)
    if not row: raise HTTPException(status_code=400,detail="Invalid or expired reset token")
    user=db.get(User,row.user_id)
    if not user: raise HTTPException(status_code=404,detail="User not found")
    user.password_hash=hash_password(payload.new_password); db.commit(); return {"ok":True}

@app.post("/api/auth/mfa/setup")
def mfa_setup(principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    user=db.get(User,principal.user_id); secret=generate_secret(); user.mfa_secret_encrypted=encrypt_json({"secret":secret}); user.mfa_enabled=False; db.commit()
    return {"secret":secret,"provisioning_uri":provisioning_uri(secret,user.email)}

@app.post("/api/auth/mfa/enable")
def mfa_enable(payload:MFASetupConfirm, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    user=db.get(User,principal.user_id); secret=decrypt_json(user.mfa_secret_encrypted).get("secret","")
    if not secret or not verify_totp(secret,payload.code): raise HTTPException(status_code=400,detail="Invalid MFA code")
    user.mfa_enabled=True; record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=user.id,action="mfa.enabled"); db.commit(); return {"ok":True}

@app.post("/api/auth/mfa/disable")
def mfa_disable(payload:MFASetupConfirm, principal:Principal=Depends(get_principal), db:Session=Depends(get_db)):
    user=db.get(User,principal.user_id); secret=decrypt_json(user.mfa_secret_encrypted).get("secret","")
    if not user.mfa_enabled or not verify_totp(secret,payload.code): raise HTTPException(status_code=400,detail="Invalid MFA code")
    user.mfa_enabled=False; user.mfa_secret_encrypted=""; record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=user.id,action="mfa.disabled"); db.commit(); return {"ok":True}

@app.get("/api/organization/members")
def organization_members(principal:Principal=Depends(require_admin), db:Session=Depends(get_db)):
    rows=db.execute(select(Membership,User).join(User,Membership.user_id==User.id).where(Membership.tenant_id==principal.tenant_id)).all()
    return [{"id":m.id,"user_id":u.id,"email":u.email,"display_name":u.display_name,"role":m.role.value,"email_verified":u.email_verified} for m,u in rows]

@app.post("/api/organization/invitations",status_code=201)
def create_invitation(payload:InviteCreate, principal:Principal=Depends(require_admin), db:Session=Depends(get_db)):
    try: require_capacity(db,principal.tenant_id,"users")
    except PermissionError as exc: raise HTTPException(status_code=402,detail=str(exc)) from exc
    email=str(payload.email).lower()
    existing=db.scalar(select(User).where(User.email==email))
    if existing and db.scalar(select(Membership).where(Membership.user_id==existing.id,Membership.tenant_id==principal.tenant_id)):
        raise HTTPException(status_code=409,detail="User is already a member")
    token=create_auth_token(db,AuthTokenType.INVITATION,tenant_id=principal.tenant_id,email=email,role=payload.role,ttl_minutes=10080)
    record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="organization.invitation.created",target_type="email",target_id=email,metadata={"role":payload.role}); db.commit()
    if email_configured():
        try: send_email(email,"You're invited to Royal Guardian",f"Accept your invitation: {settings.public_base_url.rstrip('/')}/app?invite={token}")
        except EmailDeliveryError: pass
    result={"ok":True,"email":email}
    if not settings.production: result["development_invitation_token"]=token
    return result

@app.post("/api/organization/invitations/accept")
def accept_invitation(payload:InviteAccept, response:Response, db:Session=Depends(get_db)):
    row=consume_auth_token(db,payload.token,AuthTokenType.INVITATION)
    if not row: raise HTTPException(status_code=400,detail="Invalid or expired invitation")
    user=db.scalar(select(User).where(User.email==row.email))
    if not user:
        user=User(email=row.email,password_hash=hash_password(payload.password),display_name=payload.display_name,email_verified=True); db.add(user); db.flush()
    if db.scalar(select(Membership).where(Membership.user_id==user.id,Membership.tenant_id==row.tenant_id)):
        raise HTTPException(status_code=409,detail="Already a member")
    role=Role.ADMIN if row.role=="admin" else Role.MEMBER
    membership=Membership(tenant_id=row.tenant_id,user_id=user.id,role=role); db.add(membership); db.commit()
    token=create_session(db,user,membership); response.set_cookie("rg_session",token,httponly=True,samesite="lax",secure=settings.production,max_age=settings.session_ttl_seconds)
    return {"ok":True,"tenant_id":row.tenant_id,"role":role.value}

@app.delete("/api/devices/{device_id}")
def revoke_device(device_id:str, principal:Principal=Depends(require_admin), db:Session=Depends(get_db)):
    d=db.scalar(select(Device).where(Device.id==device_id,Device.tenant_id==principal.tenant_id))
    if not d: raise HTTPException(status_code=404,detail="Device not found")
    d.status=DeviceStatus.REVOKED; d.auth_token_hash=random_token(32); record_audit(db,tenant_id=principal.tenant_id,actor_type="user",actor_id=principal.user_id,action="device.revoked",target_type="device",target_id=d.id); db.commit(); return {"ok":True}

@app.post("/api/workflows/{workflow_id}/run",status_code=202)
def run_workflow(workflow_id:str,payload:WorkflowRunCreate,principal:Principal=Depends(get_principal),db:Session=Depends(get_db)):
    from royal_guardian.services.workflows import queue_workflow
    w=db.scalar(select(Workflow).where(Workflow.id==workflow_id,Workflow.tenant_id==principal.tenant_id))
    if not w: raise HTTPException(status_code=404,detail="Workflow not found")
    row=queue_workflow(db,w,principal.user_id,payload.input); db.commit(); return {"run_id":row.id,"status":row.status.value}

@app.put("/api/workflows/{workflow_id}/schedule")
def update_workflow_schedule(workflow_id:str,payload:WorkflowScheduleUpdate,principal:Principal=Depends(get_principal),db:Session=Depends(get_db)):
    w=db.scalar(select(Workflow).where(Workflow.id==workflow_id,Workflow.tenant_id==principal.tenant_id))
    if not w: raise HTTPException(status_code=404,detail="Workflow not found")
    w.enabled=payload.enabled; w.schedule_interval_seconds=payload.interval_seconds; w.trigger_type="schedule" if payload.interval_seconds else "manual"; w.next_run_at=(datetime.now(timezone.utc)+timedelta(seconds=payload.interval_seconds)) if payload.interval_seconds and payload.enabled else None; db.commit()
    return {"id":w.id,"enabled":w.enabled,"interval_seconds":w.schedule_interval_seconds,"next_run_at":w.next_run_at.isoformat() if w.next_run_at else None}

@app.get("/api/workflow-runs")
def workflow_runs(principal:Principal=Depends(get_principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(WorkflowRun).where(WorkflowRun.tenant_id==principal.tenant_id).order_by(WorkflowRun.created_at.desc()).limit(200)).all()
    return [{"id":r.id,"workflow_id":r.workflow_id,"status":r.status.value,"input":r.input_json,"output":r.output_json,"error":r.error,"attempts":r.attempts,"created_at":r.created_at.isoformat()} for r in rows]
