# Data Model

Current core entities:

- `Tenant`: personal workspace or business organization.
- `User`: human account.
- `Membership`: user role within a tenant.
- `Session`: opaque server-side session record.
- `Agent`: tenant-owned structured agent configuration.
- `AuditEvent`: tenant-scoped action record.
- `EnrollmentToken`: single-use, expiring endpoint enrollment secret (stored hashed).
- `Device`: enrolled endpoint with hashed device credential and latest diagnostics.
- `DeviceCommand`: allowlisted command queued for a specific device.

Future entities include subscriptions/entitlements, approvals, workflows, workflow runs, integrations/connections, encrypted secrets, documents/chunks, agent memory, conversations/messages, incidents, templates and marketplace products.
