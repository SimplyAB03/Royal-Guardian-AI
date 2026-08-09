# Current State — Royal Guardian 0.4.0

Royal Guardian is now a **beta-candidate commercial codebase**, not merely the original local diagnostic prototype.

## Functional today in source

- Premium web/SaaS shell and API.
- Account registration/login, email verification, password reset and TOTP MFA.
- Personal/business tenants, RBAC and employee invitations.
- Agent definitions and provider-neutral Anthropic/OpenAI/Gemini runtime.
- Controlled tool calling and persistent human approvals.
- Google/Microsoft OAuth, token refresh, mailbox/calendar reads and approval-gated sends/event creation.
- Knowledge and scoped memory.
- Durable workflow queue, scheduler and standalone worker.
- Stripe checkout/portal/webhook lifecycle and plan entitlements.
- SMTP transactional email integration.
- Secure device enrollment, diagnostics, heartbeat, commands and device revocation.
- Windows endpoint allowlisted remediation with no arbitrary model-generated shell execution.
- Windows service/DPAPI/update-verification packaging foundation.
- PostgreSQL/Docker web+worker topology.
- Versioned database compatibility migration runner.
- Audit trail and browser security headers/origin controls.

## Still blocked from public paid production

The source cannot by itself create third-party accounts or produce a trusted Windows release from this Linux/offline environment. A real launch still requires: cloud/domain/TLS, production PostgreSQL/secrets/backups/monitoring, AI keys, Google OAuth app, Microsoft Entra app, Stripe products/prices/webhooks, SMTP provider, Windows release host, Authenticode certificate, signed EXE/MSI clean-machine testing and signed update hosting.

See `RELEASE_REPORT.md` and `FEATURE_MATRIX.md` for the launch gate.
