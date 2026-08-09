# Repository Structure

```text
Royal-Guardian-Source/
├── royal_guardian/          # SaaS platform backend
│   ├── api/                 # FastAPI HTTP interface
│   ├── core/                # configuration/security primitives
│   ├── db/                  # SQLAlchemy persistence
│   ├── integrations/        # external-provider contracts/catalog
│   ├── services/            # auth, audit, AI-provider services
│   └── tools/               # controlled tool framework
├── web/                     # public + authenticated web application
├── endpoint/                # endpoint diagnostics, actions and cloud client
├── engine/                  # retained legacy diagnostic orchestration
├── modules/                 # retained Windows diagnostic modules
├── guardian_ai/             # retained deterministic summary logic
├── core/                    # retained legacy utilities
├── ui/                      # retained PySide6 prototype UI
├── docs/                    # architecture, security, release truth
├── tests/                   # automated foundation tests
├── run_server.py            # local SaaS entry point
└── endpoint_cli.py          # endpoint development entry point
```

Long-term, the legacy `core/`, `ui/`, `engine/`, and `modules/` code should be consolidated into the endpoint package after Windows regression testing; it is preserved now to avoid discarding working diagnostics.
