from __future__ import annotations
import hashlib, hmac, json, os, time, urllib.parse, urllib.request
from royal_guardian.core.config import settings

PLAN_ENTITLEMENTS = {
 "free": {"max_agents":1,"max_users":1,"max_devices":0,"voice_enabled":False,"business_enabled":False,"endpoint_agent":False},
 "personal": {"max_agents":5,"max_users":1,"max_devices":1,"voice_enabled":False,"business_enabled":False,"endpoint_agent":True},
 "pro": {"max_agents":20,"max_users":1,"max_devices":3,"voice_enabled":True,"business_enabled":False,"endpoint_agent":True},
 "business": {"max_agents":50,"max_users":25,"max_devices":50,"voice_enabled":True,"business_enabled":True,"endpoint_agent":True},
 "enterprise": {"max_agents":1000,"max_users":1000,"max_devices":5000,"voice_enabled":True,"business_enabled":True,"endpoint_agent":True},
 "it_device": {"max_agents":5,"max_users":10,"max_devices":10,"voice_enabled":False,"business_enabled":True,"endpoint_agent":True},
}

def entitlements(plan: str) -> dict: return PLAN_ENTITLEMENTS.get(plan, PLAN_ENTITLEMENTS["free"])

def _stripe_post(path: str, fields: dict) -> dict:
    key = os.getenv("STRIPE_SECRET_KEY","")
    if not key: raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    req=urllib.request.Request("https://api.stripe.com"+path,data=urllib.parse.urlencode(fields).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/x-www-form-urlencoded"},method="POST")
    with urllib.request.urlopen(req,timeout=30) as resp: return json.loads(resp.read().decode())

def create_checkout(*, tenant_id:str, user_email:str, plan:str, success_url:str, cancel_url:str) -> dict:
    price=os.getenv(f"STRIPE_PRICE_{plan.upper()}","")
    if not price: raise RuntimeError(f"STRIPE_PRICE_{plan.upper()} is not configured")
    return _stripe_post("/v1/checkout/sessions", {"mode":"subscription","customer_email":user_email,"line_items[0][price]":price,"line_items[0][quantity]":"1","success_url":success_url,"cancel_url":cancel_url,"metadata[tenant_id]":tenant_id,"metadata[plan]":plan,"subscription_data[metadata][tenant_id]":tenant_id,"subscription_data[metadata][plan]":plan})

def create_portal(customer_id:str, return_url:str) -> dict:
    return _stripe_post("/v1/billing_portal/sessions", {"customer":customer_id,"return_url":return_url})

def verify_webhook(payload: bytes, signature: str, tolerance:int=300) -> bool:
    secret=os.getenv("STRIPE_WEBHOOK_SECRET","")
    if not secret: return False
    parts={}
    for item in signature.split(","):
        if "=" in item:
            k,v=item.split("=",1); parts.setdefault(k,[]).append(v)
    try: ts=int(parts.get("t",["0"])[0])
    except ValueError: return False
    if abs(int(time.time())-ts)>tolerance: return False
    expected=hmac.new(secret.encode(),str(ts).encode()+b"."+payload,hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected,v) for v in parts.get("v1",[]))


def plan_from_price(price_id: str) -> str:
    for plan in PLAN_ENTITLEMENTS:
        if os.getenv(f"STRIPE_PRICE_{plan.upper()}","") == price_id:
            return plan
    return "free"
