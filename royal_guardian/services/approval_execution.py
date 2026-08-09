from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from royal_guardian.db.models import Approval, Device, DeviceCommand
from royal_guardian.services.integration_tools import gmail_send, google_calendar_create, outlook_send, microsoft_calendar_create
from endpoint.actions import ACTIONS


def execute_approved(db: Session, approval: Approval, approver_id: str) -> dict:
    p=approval.parameters or {}
    tenant_id=approval.tenant_id
    user_id=approval.requester_id
    if approval.tool_id=="device_action":
        device=db.scalar(select(Device).where(Device.id==p.get("device_id"), Device.tenant_id==tenant_id))
        if not device: return {"ok":False,"error":"Target device no longer exists"}
        action=ACTIONS.get(p.get("action_id"))
        if not action: return {"ok":False,"error":"Action is no longer allowlisted"}
        cmd=DeviceCommand(tenant_id=tenant_id,device_id=device.id,action_id=p["action_id"],parameters=p.get("parameters") or {},risk=action["risk"],created_by=approver_id)
        db.add(cmd); db.flush()
        return {"ok":True,"queued_command_id":cmd.id}
    if approval.tool_id=="gmail_send": return gmail_send(db,tenant_id,user_id,str(p.get("to","")),str(p.get("subject","")),str(p.get("body","")))
    if approval.tool_id=="google_calendar_create": return google_calendar_create(db,tenant_id,user_id,str(p.get("summary","")),str(p.get("start","")),str(p.get("end","")),str(p.get("timezone","UTC")),str(p.get("description","")))
    if approval.tool_id=="outlook_send": return outlook_send(db,tenant_id,user_id,str(p.get("to","")),str(p.get("subject","")),str(p.get("body","")))
    if approval.tool_id=="microsoft_calendar_create": return microsoft_calendar_create(db,tenant_id,user_id,str(p.get("subject","")),str(p.get("start","")),str(p.get("end","")),str(p.get("timezone","UTC")),str(p.get("body","")))
    return {"ok":False,"error":"Unsupported approved tool"}
