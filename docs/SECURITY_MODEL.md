# Security Model

## Implemented controls
- PBKDF2-HMAC-SHA256 password hashing with unique random salts.
- Opaque random login sessions; database stores only token hashes.
- HttpOnly, SameSite=Lax session cookie. `Secure` is enabled in production mode.
- Production startup refuses the known default session secret.
- Backend RBAC for administrative endpoints.
- Tenant filters on tenant-owned API queries.
- Expiring, single-use device enrollment tokens.
- Hashed long-lived endpoint credentials.
- Endpoint action allowlist; no model-generated arbitrary command execution.
- Explicit approval flag required before medium/high-risk device commands can be queued.
- Audit records for account/session/agent/device/command events.

## Highest outstanding risks before production
1. Add CSRF token protection for state-changing cookie-authenticated requests.
2. Add rate limiting and login lockout/abuse protections.
3. Add email verification and robust account recovery.
4. Introduce encrypted-at-rest integration secret storage backed by KMS/secret manager.
5. Add MFA and enterprise SSO options.
6. Add immutable/tamper-evident audit retention strategy.
7. Add real PostgreSQL row-level/tenant isolation defense-in-depth where appropriate.
8. Perform external penetration testing and dependency/SBOM scanning.
9. Build signed Windows service and signed update chain.
10. Threat-model prompt injection before enabling external-content autonomous actions.

## Prompt injection rule
External content is data, never policy. Email/document/web content may influence task data but cannot change tool permission, tenant, approval or secret-access rules.
