from __future__ import annotations
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from royal_guardian.db.models import KnowledgeDocument, MemoryItem

def _terms(q:str)->set[str]: return {x for x in re.findall(r"[a-zA-Z0-9_]{3,}", q.lower())}
def _score(text:str, terms:set[str])->int:
    low=text.lower(); return sum(low.count(t) for t in terms)

def search_knowledge(db:Session, tenant_id:str, query:str, agent_id:str="", limit:int=5)->list[dict]:
    terms=_terms(query)
    rows=db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.tenant_id==tenant_id)).all()
    ranked=[]
    for r in rows:
        if r.agent_id and agent_id and r.agent_id!=agent_id: continue
        s=_score(r.content_text,terms)
        if s: ranked.append((s,r))
    ranked.sort(key=lambda x:x[0],reverse=True)
    return [{"id":r.id,"name":r.name,"excerpt":r.content_text[:1800]} for _,r in ranked[:limit]]

def search_memory(db:Session, tenant_id:str, query:str, agent_id:str="", limit:int=5)->list[dict]:
    terms=_terms(query)
    rows=db.scalars(select(MemoryItem).where(MemoryItem.tenant_id==tenant_id)).all()
    ranked=[]
    for r in rows:
        if r.scope=="agent" and agent_id and r.agent_id and r.agent_id!=agent_id: continue
        s=_score(r.content,terms)
        if s: ranked.append((s,r))
    ranked.sort(key=lambda x:x[0],reverse=True)
    return [{"id":r.id,"scope":r.scope,"key":r.key,"content":r.content[:1200]} for _,r in ranked[:limit]]
