# Testing

Automated tests currently cover:
- password hash/verify behavior
- tenant isolation at persistence-query level
- API registration/session/agent flow
- explicit absence of arbitrary-shell endpoint tools

Before production add:
- full API tenant isolation matrix
- CSRF tests
- rate-limit/auth abuse tests
- PostgreSQL integration suite
- endpoint enrollment replay/revocation tests
- device command ownership/approval tests
- real Windows VM action tests
- OAuth state/PKCE/token-refresh tests
- Stripe webhook replay/idempotency tests
- browser E2E suite
