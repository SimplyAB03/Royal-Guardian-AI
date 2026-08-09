# Royal Guardian Architecture

## Product boundary
Royal Guardian is designed as a cloud SaaS platform plus optional endpoint clients. The web application is the customer-facing control plane. Royal Guardian IT adds a Windows endpoint that reports diagnostics and executes only cloud-authorized, allowlisted actions.

## Current component map

```text
Browser
  |
  v
FastAPI web/API (`royal_guardian/api`)
  |---- authentication / tenant authorization
  |---- agents
  |---- integration catalog
  |---- device enrollment and command queue
  |---- audit log
  v
SQLAlchemy persistence (`royal_guardian/db`)

Windows Endpoint (`endpoint/`)
  |---- local diagnostics
  |---- authenticated heartbeat
  |---- command poll
  |---- allowlisted action dispatcher
  v
Royal Guardian API

Legacy diagnostic engine (`engine/`, `modules/`)
  retained for Windows-specific Royal Guardian IT work
```

## Target architecture

```text
Web / Desktop / Voice Channels
            |
        API Gateway
            |
 -------------------------------------------------
 | Auth/Tenancy | Agent Runtime | Workflow Engine |
 | Tools        | Approvals     | Knowledge/RAG   |
 | Integrations | Billing       | Audit/Analytics |
 -------------------------------------------------
            |
 PostgreSQL / Queue / Object Storage / Vector Store
            |
 Windows Endpoint / External SaaS APIs / Telephony
```

## Security boundaries
1. The model never receives raw OAuth refresh tokens or provider secrets.
2. Tool authorization is performed by application code before execution.
3. Device actions are selected from an explicit allowlist; arbitrary shell execution is absent.
4. Device enrollment credentials are single-use and time-limited.
5. Permanent device credentials are random and stored server-side only as SHA-256 hashes.
6. All tenant-owned resources include tenant identity and API queries scope by the authenticated tenant.
7. Administrative APIs require role checks in backend code.

## Database portability
Local development defaults to SQLite. Models use SQLAlchemy and are intended to move to PostgreSQL for production. Before production, add Alembic migrations and PostgreSQL-specific integration tests.

## Provider abstraction
`royal_guardian/integrations` establishes provider/status contracts. Live OAuth/AI adapters remain external-setup blockers and must be implemented and verified one provider at a time.
