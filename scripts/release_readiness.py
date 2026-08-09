from __future__ import annotations
import os
from pathlib import Path

CHECKS={
 "RG_SESSION_SECRET": lambda v: bool(v and v!="change-me-in-production" and len(v)>=32),
 "RG_ENCRYPTION_SECRET": lambda v: bool(v and v!="change-me-in-production" and len(v)>=32 and v!=os.getenv("RG_SESSION_SECRET")),
 "RG_PUBLIC_BASE_URL": lambda v: bool(v and v.startswith("https://")),
 "STRIPE_SECRET_KEY": bool,
 "STRIPE_WEBHOOK_SECRET": bool,
 "GOOGLE_CLIENT_ID": bool,
 "GOOGLE_CLIENT_SECRET": bool,
 "MICROSOFT_CLIENT_ID": bool,
 "MICROSOFT_CLIENT_SECRET": bool,
 "SMTP_HOST": bool,
 "SMTP_FROM": bool,
}

def main():
    failures=[]
    for name,check in CHECKS.items():
        value=os.getenv(name,"")
        ok=check(value)
        print(f"{'PASS' if ok else 'MISSING'}  {name}")
        if not ok: failures.append(name)
    artifacts=[Path("dist/RoyalGuardianSetup.exe"),Path("dist/RoyalGuardian.msi")]
    for artifact in artifacts:
        ok=artifact.exists()
        print(f"{'PASS' if ok else 'MISSING'}  {artifact}")
        if not ok: failures.append(str(artifact))
    print("\nREADY" if not failures else "\nNOT READY: external/configuration requirements remain")
    return 0 if not failures else 1
if __name__=="__main__": raise SystemExit(main())
