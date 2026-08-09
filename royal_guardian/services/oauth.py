from __future__ import annotations
import json, os, time, urllib.parse, urllib.request
from dataclasses import dataclass
from sqlalchemy.orm import Session
from royal_guardian.core.config import settings
from royal_guardian.core.security import sign_payload, verify_signed_payload
from royal_guardian.db.models import IntegrationConnection
from royal_guardian.services.secrets import decrypt_json, encrypt_json

@dataclass(frozen=True)
class OAuthProvider:
    id: str
    authorize_url: str
    token_url: str
    client_id_env: str
    client_secret_env: str
    scopes: tuple[str, ...]

PROVIDERS = {
    "google": OAuthProvider("google", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", ("openid","email","profile","https://www.googleapis.com/auth/gmail.modify","https://www.googleapis.com/auth/calendar","https://www.googleapis.com/auth/drive.readonly")),
    "microsoft": OAuthProvider("microsoft", "https://login.microsoftonline.com/common/oauth2/v2.0/authorize", "https://login.microsoftonline.com/common/oauth2/v2.0/token", "MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET", ("openid","email","profile","offline_access","User.Read","Mail.ReadWrite","Mail.Send","Calendars.ReadWrite","Files.Read")),
}

def callback_url(provider: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/api/oauth/{provider}/callback"

def authorization_url(provider_id: str, user_id: str, tenant_id: str) -> str:
    p = PROVIDERS[provider_id]
    client_id = os.getenv(p.client_id_env, "")
    if not client_id: raise RuntimeError(f"{p.client_id_env} is not configured")
    state = sign_payload(f"{provider_id}:{tenant_id}:{user_id}", int(time.time()) + 600)
    params = {"client_id": client_id, "redirect_uri": callback_url(provider_id), "response_type": "code", "scope": " ".join(p.scopes), "state": state, "access_type": "offline", "prompt": "consent"}
    return p.authorize_url + "?" + urllib.parse.urlencode(params)

def _post_token(provider_id: str, body: dict) -> dict:
    p=PROVIDERS[provider_id]
    req=urllib.request.Request(p.token_url,data=urllib.parse.urlencode(body).encode(),headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    with urllib.request.urlopen(req,timeout=30) as resp: return json.loads(resp.read().decode())

def exchange_code(provider_id: str, code: str) -> dict:
    p = PROVIDERS[provider_id]
    body = {"client_id": os.getenv(p.client_id_env,""), "client_secret": os.getenv(p.client_secret_env,""), "code": code, "redirect_uri": callback_url(provider_id), "grant_type": "authorization_code"}
    if provider_id == "microsoft": body["scope"] = " ".join(p.scopes)
    tokens=_post_token(provider_id,body)
    if "expires_in" in tokens: tokens["expires_at"]=int(time.time())+int(tokens["expires_in"])-60
    return tokens

def refresh_tokens(provider_id: str, tokens: dict) -> dict:
    refresh=tokens.get("refresh_token")
    if not refresh: raise RuntimeError(f"{provider_id} connection has no refresh token; reconnect it")
    p=PROVIDERS[provider_id]
    body={"client_id":os.getenv(p.client_id_env,""),"client_secret":os.getenv(p.client_secret_env,""),"refresh_token":refresh,"grant_type":"refresh_token"}
    if provider_id=="microsoft": body["scope"]=" ".join(p.scopes)
    new=_post_token(provider_id,body)
    merged={**tokens,**new}
    if not new.get("refresh_token"): merged["refresh_token"]=refresh
    if "expires_in" in merged: merged["expires_at"]=int(time.time())+int(merged["expires_in"])-60
    return merged

def usable_access_token(db: Session, connection: IntegrationConnection) -> str:
    tokens=decrypt_json(connection.encrypted_tokens)
    if not tokens.get("access_token"): raise RuntimeError(f"{connection.provider} connection has no access token")
    if int(tokens.get("expires_at",0) or 0) and int(tokens["expires_at"]) <= int(time.time()):
        tokens=refresh_tokens(connection.provider,tokens)
        connection.encrypted_tokens=encrypt_json(tokens)
        db.add(connection); db.flush()
    return str(tokens["access_token"])

def parse_state(state: str, expected_provider: str) -> tuple[str,str] | None:
    value = verify_signed_payload(state)
    if not value: return None
    try:
        provider, tenant_id, user_id = value.split(":",2)
        return (tenant_id,user_id) if provider == expected_provider else None
    except ValueError: return None
