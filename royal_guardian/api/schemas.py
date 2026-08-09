from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    display_name: str = Field(min_length=1, max_length=160)
    organization_name: str | None = Field(default=None, max_length=160)
    is_business: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    role_prompt: str = Field(default="", max_length=20000)
    objectives: list[str] = []
    tools: list[str] = []
    approval_rules: dict = {}
    model_provider: str = "anthropic"
    model_name: str = ""


class EnrollmentCreate(BaseModel):
    ttl_minutes: int = Field(default=15, ge=1, le=1440)


class DeviceEnroll(BaseModel):
    enrollment_token: str
    name: str = Field(min_length=1, max_length=160)
    fingerprint: str = Field(min_length=8, max_length=128)
    platform: str = "windows"


class DeviceHeartbeat(BaseModel):
    diagnostics: dict = {}


class CommandCreate(BaseModel):
    action_id: str
    parameters: dict = {}
    approved: bool = False


class CommandResult(BaseModel):
    ok: bool
    result: dict = {}
    error: str | None = None


class AgentRunRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    max_tokens: int = Field(default=1024, ge=64, le=8192)

class ApprovalDecision(BaseModel):
    approve: bool
    reason: str = Field(default="", max_length=4000)

class MemoryCreate(BaseModel):
    agent_id: str = ""
    scope: str = Field(default="agent", pattern="^(user|agent|organization)$")
    key: str = Field(default="", max_length=160)
    content: str = Field(min_length=1, max_length=20000)

class KnowledgeCreate(BaseModel):
    agent_id: str = ""
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=500000)
    mime_type: str = Field(default="text/plain", max_length=128)

class WorkflowCreate(BaseModel):
    agent_id: str = ""
    name: str = Field(min_length=1, max_length=160)
    trigger_type: str = Field(default="manual", max_length=64)
    definition: dict = {}
    enabled: bool = True

class CheckoutCreate(BaseModel):
    plan: str = Field(pattern="^(personal|pro|business|enterprise|it_device)$")
    success_url: str | None = None
    cancel_url: str | None = None

class MFASetupConfirm(BaseModel):
    code: str = Field(min_length=6, max_length=8)

class LoginMFARequest(LoginRequest):
    mfa_code: str | None = Field(default=None, min_length=6, max_length=8)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=256)

class VerifyEmailRequest(BaseModel):
    token: str

class InviteCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(member|admin)$")

class InviteAccept(BaseModel):
    token: str
    display_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=10, max_length=256)

class WorkflowRunCreate(BaseModel):
    input: dict = {}

class WorkflowScheduleUpdate(BaseModel):
    interval_seconds: int = Field(default=0, ge=0, le=31536000)
    enabled: bool = True
