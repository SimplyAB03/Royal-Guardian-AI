from __future__ import annotations
import base64, json, urllib.parse, urllib.request
from sqlalchemy import select
from sqlalchemy.orm import Session
from royal_guardian.db.models import IntegrationConnection
from royal_guardian.services.oauth import usable_access_token

class IntegrationToolError(RuntimeError): pass

def _connection(db:Session,tenant_id:str,user_id:str,provider:str)->tuple[IntegrationConnection,str]:
    c=db.scalar(select(IntegrationConnection).where(IntegrationConnection.tenant_id==tenant_id,IntegrationConnection.user_id==user_id,IntegrationConnection.provider==provider,IntegrationConnection.status=="connected"))
    if not c: raise IntegrationToolError(f"{provider} is not connected for this user")
    try: token=usable_access_token(db,c)
    except Exception as exc: raise IntegrationToolError(str(exc)) from exc
    return c,token

def _request(url:str,token:str,*,method:str="GET",payload:dict|None=None,headers:dict|None=None)->dict:
    hdr={"Authorization":f"Bearer {token}","Accept":"application/json","User-Agent":"RoyalGuardian/0.4"}
    hdr.update(headers or {})
    data=None
    if payload is not None:
        data=json.dumps(payload).encode(); hdr["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=data,headers=hdr,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read().decode(); return json.loads(raw) if raw else {"ok":True}
    except Exception as exc: raise IntegrationToolError(f"Integration request failed: {exc}") from exc

def gmail_search(db:Session,tenant_id:str,user_id:str,query:str,max_results:int=10)->dict:
    _,tok=_connection(db,tenant_id,user_id,"google")
    qs=urllib.parse.urlencode({"q":query,"maxResults":min(max(max_results,1),20)})
    listing=_request("https://gmail.googleapis.com/gmail/v1/users/me/messages?"+qs,tok)
    messages=[]
    for item in listing.get("messages",[])[:10]:
        m=_request(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date",tok)
        hs={h.get('name','').lower():h.get('value','') for h in m.get('payload',{}).get('headers',[])}
        messages.append({"id":m.get("id"),"thread_id":m.get("threadId"),"from":hs.get("from",""),"subject":hs.get("subject",""),"date":hs.get("date",""),"snippet":m.get("snippet","")})
    return {"ok":True,"messages":messages}

def gmail_send(db:Session,tenant_id:str,user_id:str,to:str,subject:str,body:str)->dict:
    _,tok=_connection(db,tenant_id,user_id,"google")
    raw=f"To: {to}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body}".encode()
    encoded=base64.urlsafe_b64encode(raw).decode().rstrip("=")
    data=_request("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",tok,method="POST",payload={"raw":encoded})
    return {"ok":True,"message_id":data.get("id"),"thread_id":data.get("threadId")}

def google_calendar_list(db:Session,tenant_id:str,user_id:str,max_results:int=10)->dict:
    _,tok=_connection(db,tenant_id,user_id,"google")
    qs=urllib.parse.urlencode({"maxResults":min(max(max_results,1),20),"singleEvents":"true","orderBy":"startTime","timeMin":__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
    data=_request("https://www.googleapis.com/calendar/v3/calendars/primary/events?"+qs,tok)
    return {"ok":True,"events":[{"id":e.get("id"),"summary":e.get("summary",""),"start":e.get("start",{}),"end":e.get("end",{}),"location":e.get("location","")} for e in data.get("items",[])]}

def google_calendar_create(db:Session,tenant_id:str,user_id:str,summary:str,start:str,end:str,timezone_name:str="UTC",description:str="")->dict:
    _,tok=_connection(db,tenant_id,user_id,"google")
    payload={"summary":summary,"description":description,"start":{"dateTime":start,"timeZone":timezone_name},"end":{"dateTime":end,"timeZone":timezone_name}}
    data=_request("https://www.googleapis.com/calendar/v3/calendars/primary/events",tok,method="POST",payload=payload)
    return {"ok":True,"event_id":data.get("id"),"html_link":data.get("htmlLink")}

def outlook_search(db:Session,tenant_id:str,user_id:str,query:str,top:int=10)->dict:
    _,tok=_connection(db,tenant_id,user_id,"microsoft")
    qs=urllib.parse.urlencode({"$search":f'"{query}"',"$top":min(max(top,1),20),"$select":"id,subject,from,receivedDateTime,bodyPreview"})
    data=_request("https://graph.microsoft.com/v1.0/me/messages?"+qs,tok,headers={"ConsistencyLevel":"eventual"})
    return {"ok":True,"messages":[{"id":m.get("id"),"subject":m.get("subject",""),"from":m.get("from",{}),"received":m.get("receivedDateTime"),"preview":m.get("bodyPreview","")} for m in data.get("value",[])]}

def outlook_send(db:Session,tenant_id:str,user_id:str,to:str,subject:str,body:str)->dict:
    _,tok=_connection(db,tenant_id,user_id,"microsoft")
    payload={"message":{"subject":subject,"body":{"contentType":"Text","content":body},"toRecipients":[{"emailAddress":{"address":to}}]},"saveToSentItems":True}
    _request("https://graph.microsoft.com/v1.0/me/sendMail",tok,method="POST",payload=payload)
    return {"ok":True}

def microsoft_calendar_list(db:Session,tenant_id:str,user_id:str,top:int=10)->dict:
    _,tok=_connection(db,tenant_id,user_id,"microsoft")
    qs=urllib.parse.urlencode({"$top":min(max(top,1),20),"$orderby":"start/dateTime","$select":"id,subject,start,end,location,organizer"})
    data=_request("https://graph.microsoft.com/v1.0/me/events?"+qs,tok)
    return {"ok":True,"events":data.get("value",[])}

def microsoft_calendar_create(db:Session,tenant_id:str,user_id:str,subject:str,start:str,end:str,timezone_name:str="UTC",body:str="")->dict:
    _,tok=_connection(db,tenant_id,user_id,"microsoft")
    payload={"subject":subject,"body":{"contentType":"Text","content":body},"start":{"dateTime":start,"timeZone":timezone_name},"end":{"dateTime":end,"timeZone":timezone_name}}
    data=_request("https://graph.microsoft.com/v1.0/me/events",tok,method="POST",payload=payload)
    return {"ok":True,"event_id":data.get("id"),"web_link":data.get("webLink")}
