from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from royal_guardian.db.models import Workflow, WorkflowRun, WorkflowRunStatus, Agent, AgentRun, Approval, ApprovalStatus
from royal_guardian.services.runtime import run_agent_runtime
from royal_guardian.services.audit import record_audit


def queue_workflow(db:Session, workflow:Workflow, requested_by:str, input_json:dict|None=None) -> WorkflowRun:
    row=WorkflowRun(tenant_id=workflow.tenant_id,workflow_id=workflow.id,agent_id=workflow.agent_id,requested_by=requested_by,input_json=input_json or {})
    db.add(row); db.flush()
    record_audit(db,tenant_id=workflow.tenant_id,actor_type="user" if requested_by else "system",actor_id=requested_by or "scheduler",action="workflow.run.queued",target_type="workflow_run",target_id=row.id,metadata={"workflow_id":workflow.id})
    return row


def queue_due_schedules(db:Session, now:datetime|None=None) -> int:
    now=now or datetime.now(timezone.utc)
    rows=db.scalars(select(Workflow).where(Workflow.enabled.is_(True),Workflow.trigger_type=="schedule",Workflow.schedule_interval_seconds>0,Workflow.next_run_at.is_not(None),Workflow.next_run_at<=now)).all()
    count=0
    for w in rows:
        queue_workflow(db,w,w.owner_id,{"trigger":"schedule"})
        w.next_run_at=now+timedelta(seconds=w.schedule_interval_seconds)
        count+=1
    db.commit(); return count


def execute_one(db:Session, run:WorkflowRun) -> WorkflowRun:
    if run.status != WorkflowRunStatus.QUEUED: return run
    run.status=WorkflowRunStatus.RUNNING; run.started_at=datetime.now(timezone.utc); run.attempts+=1; db.commit()
    try:
        workflow=db.scalar(select(Workflow).where(Workflow.id==run.workflow_id,Workflow.tenant_id==run.tenant_id))
        if not workflow or not workflow.enabled: raise RuntimeError("Workflow missing or disabled")
        definition=workflow.definition or {}
        if not workflow.agent_id: raise RuntimeError("Workflow has no agent")
        agent=db.scalar(select(Agent).where(Agent.id==workflow.agent_id,Agent.tenant_id==run.tenant_id))
        if not agent: raise RuntimeError("Workflow agent missing")
        prompt=str(definition.get("prompt") or run.input_json.get("message") or "Run this workflow according to your configured objectives.")
        ar=AgentRun(tenant_id=run.tenant_id,agent_id=agent.id,user_id=run.requested_by or workflow.owner_id,input_text=prompt,provider=agent.model_provider,model=agent.model_name)
        db.add(ar); db.flush()
        result=run_agent_runtime(db,agent=agent,run=ar,user_id=ar.user_id,message=prompt,max_tokens=int(definition.get("max_tokens",1024)))
        ar.output_text=result["text"]; ar.usage=result["usage"]
        pending=any(True for _ in db.scalars(select(__import__('royal_guardian.db.models',fromlist=['Approval']).Approval).where(__import__('royal_guardian.db.models',fromlist=['Approval']).Approval.run_id==ar.id,__import__('royal_guardian.db.models',fromlist=['Approval']).Approval.status==__import__('royal_guardian.db.models',fromlist=['ApprovalStatus']).ApprovalStatus.PENDING)).all())
        if pending:
            ar.status="waiting_approval"; run.status=WorkflowRunStatus.WAITING_APPROVAL
        else:
            ar.status="succeeded"; run.status=WorkflowRunStatus.SUCCEEDED; run.completed_at=datetime.now(timezone.utc)
        ar.completed_at=datetime.now(timezone.utc); run.output_json={"agent_run_id":ar.id,"text":result["text"],"usage":result["usage"]}
        db.commit(); return run
    except Exception as exc:
        db.rollback()
        fresh=db.get(WorkflowRun,run.id)
        fresh.status=WorkflowRunStatus.FAILED; fresh.error=str(exc); fresh.completed_at=datetime.now(timezone.utc); db.commit(); return fresh


def process_queue(db:Session, limit:int=10) -> int:
    queue_due_schedules(db)
    rows=db.scalars(select(WorkflowRun).where(WorkflowRun.status==WorkflowRunStatus.QUEUED,WorkflowRun.available_at<=datetime.now(timezone.utc)).order_by(WorkflowRun.created_at.asc()).limit(limit)).all()
    for row in rows: execute_one(db,row)
    return len(rows)
