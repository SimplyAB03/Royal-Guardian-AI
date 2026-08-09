# Royal Guardian 0.4.0 Release Report

## Release decision

**BETA-CANDIDATE CODEBASE — NOT YET CLEARED FOR PUBLIC PAID PRODUCTION.**

The application now contains the major software paths needed for a first commercial beta: secure account lifecycle, MFA, business invitations, paid-plan capacity enforcement, real AI runtime/tool controls, approval-gated Google/Microsoft write actions, OAuth token refresh, durable workflow scheduling/worker execution, Stripe lifecycle handling, transactional email integration, device management, and the Windows endpoint foundation.

Public launch is still blocked by external infrastructure and Windows release validation that cannot be completed inside this Linux/offline build environment.

## Working software

- SaaS website and authenticated application.
- Registration/login/session management.
- Email verification and password-reset token flows.
- TOTP MFA setup and MFA-enforced login.
- Personal/business tenants, RBAC and business invitations.
- Agent runtime for Anthropic/OpenAI/Gemini adapters.
- Controlled read tools and human-approval-gated external writes.
- Gmail search/send, Google Calendar read/create.
- Outlook search/send, Microsoft Calendar read/create.
- Automatic Google/Microsoft OAuth access-token refresh.
- Separate encryption secret for integration/MFA material.
- Knowledge and scoped memory.
- Persistent workflow queue, interval scheduler and standalone worker.
- Stripe checkout/portal/signed webhook lifecycle and entitlements.
- SMTP transactional-email provider path.
- Security headers and same-origin enforcement for browser writes.
- Windows endpoint enrollment, authentication, diagnostics, command polling and allowlisted remediation.
- Device revocation.
- Versioned schema compatibility migrations.
- PostgreSQL Docker topology with dedicated worker.

## Test results

**13 automated tests passed.**

Coverage includes the previous authentication, tenancy, API, endpoint-action and runtime tests plus:
- email verification
- password reset
- TOTP MFA
- free-plan agent limit enforcement
- paid business invitation acceptance
- durable workflow queue creation
- security response headers

Python compile check: **PASS**.

## External blockers before accepting real customer payments

1. Deploy web/API/worker/PostgreSQL to a production cloud account.
2. Configure a real HTTPS domain and TLS.
3. Store `RG_SESSION_SECRET` and separate `RG_ENCRYPTION_SECRET` in managed secrets.
4. Create and verify Google OAuth application/consent screen.
5. Create Microsoft Entra application and grant required Graph permissions.
6. Create Stripe products/prices, webhook endpoint and customer portal settings.
7. Configure SMTP/transactional email and validate deliverability.
8. Configure AI-provider production keys and budget/rate controls.
9. Build the endpoint on a Windows release host.
10. Obtain an Authenticode code-signing certificate.
11. Produce/sign/test `RoyalGuardianSetup.exe` and enterprise MSI on clean supported Windows machines.
12. Complete signed auto-update release hosting and rollback validation.
13. Add production monitoring/error tracking/backups.
14. Perform penetration/security testing before enterprise sales.
15. Prepare Terms, Privacy Policy, support process and any required AI/telephony disclosures.

Run `python scripts/release_readiness.py` in the production/release environment to surface missing configuration/artifacts.

## Known limitations

- Knowledge retrieval is lexical rather than vector/embedding based.
- Scheduler currently supports durable interval scheduling; calendar-style cron expression UX is not yet implemented.
- Workflow execution uses an agent prompt definition rather than the future visual node engine.
- Live Google/Microsoft/Stripe/AI network calls could not be executed in this offline environment.
- Windows binary/service/MSI install/update/uninstall cannot be validated on Linux.
- Voice/telephony and marketplace are post-beta expansions.

## Recommended launch gate

Call the product an **early paid beta** only after these two tests pass against production infrastructure:

1. New customer → pay → verify account → create agent → connect Google/Microsoft → perform an approval-gated real external action → audit result.
2. Business customer → pay → invite employee → download signed installer → clean Windows install → enroll device → report diagnostics → approve remediation → verify result → update → clean uninstall.
