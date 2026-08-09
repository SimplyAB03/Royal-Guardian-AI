from __future__ import annotations
import os, smtplib
from email.message import EmailMessage

class EmailDeliveryError(RuntimeError): pass

def configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))

def send_email(to: str, subject: str, text: str) -> None:
    if not configured(): raise EmailDeliveryError("SMTP is not configured")
    host=os.environ["SMTP_HOST"]; port=int(os.getenv("SMTP_PORT","587")); username=os.getenv("SMTP_USERNAME",""); password=os.getenv("SMTP_PASSWORD","")
    msg=EmailMessage(); msg["From"]=os.environ["SMTP_FROM"]; msg["To"]=to; msg["Subject"]=subject; msg.set_content(text)
    try:
        if os.getenv("SMTP_SSL","false").lower() in {"1","true","yes"}:
            with smtplib.SMTP_SSL(host,port,timeout=20) as smtp:
                if username: smtp.login(username,password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host,port,timeout=20) as smtp:
                smtp.ehlo()
                if os.getenv("SMTP_STARTTLS","true").lower() in {"1","true","yes"}: smtp.starttls(); smtp.ehlo()
                if username: smtp.login(username,password)
                smtp.send_message(msg)
    except Exception as exc: raise EmailDeliveryError(str(exc)) from exc
