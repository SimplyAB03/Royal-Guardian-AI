# Royal Guardian 0.4.0 0.3.0

Royal Guardian is evolving from a Windows diagnostic prototype into a universal AI-agent SaaS platform with Royal Guardian IT as its first packaged agent.

## What works in this build

The application now includes a real SaaS backend, web dashboard, auth/tenancy, agent runtime, controlled AI tool calling, human approvals, knowledge/memory, workflow definitions, device management, Google/Microsoft OAuth + read tools, Stripe billing paths, audit logs, and a secure Windows endpoint foundation.

The Windows endpoint can enroll, authenticate, report diagnostics, receive allowlisted commands and report results. The cloud agent runtime can request device remediation, but medium/high risk actions are persisted as approvals before a device command is ever queued.

## Run locally

```bash
python -m venv .venv
# activate it
pip install -r requirements.txt
uvicorn royal_guardian.api.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Tests

```bash
pytest -q
```

## Important production status

Do not sell this release as production-ready. Read `docs/RELEASE_REPORT.md` and `docs/FEATURE_MATRIX.md`. External OAuth/billing/AI credentials, Windows signing/building, production deployment, workflow workers and additional hardening are still required.

## Windows endpoint

Development enrollment:

```bash
python endpoint_cli.py enroll --server http://127.0.0.1:8000 --token YOUR_ENROLLMENT_TOKEN
python endpoint_cli.py run
```

Commercial packaging instructions are under `packaging/windows/` and `docs/WINDOWS_AGENT.md`.


## 0.4.0 production-completion foundation

Royal Guardian now includes MFA, email verification/password reset, business invitations, approval-gated Google/Microsoft write tools, OAuth refresh, durable workflow scheduling/worker execution, Stripe lifecycle handling, SMTP transactional email, security headers, capacity entitlements and device revocation.

Run the web service:

```bash
uvicorn royal_guardian.api.main:app --reload
```

Run the durable worker in a second process:

```bash
python -m royal_guardian.worker
```

Before any public paid launch, read `docs/RELEASE_REPORT.md` and run `python scripts/release_readiness.py`. External OAuth, Stripe, cloud, email, AI-provider, Windows signing and clean-machine installer validation still require real accounts/infrastructure.
