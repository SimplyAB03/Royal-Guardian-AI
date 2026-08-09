# Royal Guardian Feature Matrix — 0.4.0

Status definitions: **PRODUCTION**, **FUNCTIONAL**, **PARTIAL**, **PLANNED**, **BLOCKED_BY_CREDENTIALS**, **BLOCKED_BY_EXTERNAL_SETUP**.

| Capability | Status | Notes |
|---|---|---|
| Public marketing website | FUNCTIONAL | Responsive site; production copy/SEO/legal pages still need final review |
| Authenticated SaaS web app | FUNCTIONAL | Agents, chat, approvals, knowledge, automations, devices, organization, security, connections, billing, audit |
| Email/password authentication | FUNCTIONAL | PBKDF2, server sessions, password-reset tokens |
| Email verification | FUNCTIONAL | Token flow + SMTP delivery path; live delivery requires SMTP provider |
| MFA/TOTP | FUNCTIONAL | Authenticator setup, enable/disable, MFA-enforced login |
| Business membership/invitations | FUNCTIONAL | Owner/admin invitations and member acceptance with plan limits |
| Personal/business tenancy | FUNCTIONAL | Tenant-scoped data and RBAC |
| Tenant isolation | FUNCTIONAL | Backend-scoped queries + automated tests |
| Agent create/list/run | FUNCTIONAL | Plan limits enforced for agent creation |
| Multi-provider AI runtime | FUNCTIONAL | Anthropic/OpenAI/Gemini adapters; live calls require API credentials/network |
| Tool permission allowlist | FUNCTIONAL | Agent only sees registered configured tools |
| Human approvals | FUNCTIONAL | Persistent approval queue; external writes and device writes gated |
| Gmail read | FUNCTIONAL | Real Gmail API path; live verification requires Google OAuth |
| Gmail send | FUNCTIONAL | Real Gmail send API implementation, always approval-gated |
| Google Calendar read/create | FUNCTIONAL | Create is approval-gated |
| Outlook read/send | FUNCTIONAL | Real Microsoft Graph paths; send approval-gated |
| Microsoft Calendar read/create | FUNCTIONAL | Create approval-gated |
| OAuth token refresh | FUNCTIONAL | Google/Microsoft refresh tokens rotate automatically before calls |
| OAuth secret storage | FUNCTIONAL | Encrypted at rest with separate encryption secret support |
| Knowledge | FUNCTIONAL | Tenant-scoped text knowledge; vector embeddings remain later optimization |
| Scoped memory | FUNCTIONAL | User/agent/organization memory |
| Durable workflow queue | FUNCTIONAL | Persistent WorkflowRun rows + standalone worker process |
| Scheduled workflows | FUNCTIONAL | Persistent interval schedules; worker queues due runs |
| Workflow visual builder | PLANNED | JSON/guided definitions currently, full node canvas later |
| Stripe Checkout | FUNCTIONAL | Real API + subscription metadata propagation |
| Stripe webhook lifecycle | FUNCTIONAL | Signed webhooks; create/update/delete subscription handling |
| Central entitlements | FUNCTIONAL | Agent/user/device capacity enforcement on critical creation paths |
| Transactional email | FUNCTIONAL | Generic SMTP path for verification/reset/invitations |
| Audit logging | FUNCTIONAL | Security, tool, approval, integration, workflow/device activity |
| Browser security headers | FUNCTIONAL | CSP, frame denial, nosniff, referrer and permissions policy; HSTS in production |
| Browser origin/CSRF mitigation | FUNCTIONAL | State-changing browser requests validate same origin; cookies SameSite=Lax |
| Windows diagnostics | FUNCTIONAL | Existing detailed Windows modules + cloud endpoint collector |
| Secure device enrollment/auth | FUNCTIONAL | Single-use enrollment, hashed device credential, revocation |
| Device command queue | FUNCTIONAL | Cloud queue/result lifecycle |
| Allowlisted remediation | FUNCTIONAL | No arbitrary model shell execution |
| Windows DPAPI token storage | FUNCTIONAL | Endpoint credential protection on Windows |
| Windows background service | PARTIAL | Service wrapper/build scripts exist; clean-machine validation requires Windows host |
| Windows EXE/MSI | BLOCKED_BY_EXTERNAL_SETUP | Must be produced/tested on Windows; signing certificate/toolchain required |
| Signed auto-update | PARTIAL | Cryptographic verification exists; hosted signed release channel/installer swap remains |
| Voice/telephony | BLOCKED_BY_CREDENTIALS | Telephony account/number + compliance setup required |
| Agent template marketplace | PLANNED | Not required for first paid beta |
| PostgreSQL/Docker topology | FUNCTIONAL | Web + persistent worker + PostgreSQL compose stack |
| Schema migrations | FUNCTIONAL | Versioned compatibility migration runner for 0.3→0.4 schema |
| Cloud deployment | BLOCKED_BY_EXTERNAL_SETUP | Domain/cloud/TLS/managed DB/secrets/monitoring accounts required |
