# Development

Run API: `python run_server.py`

Run tests: `pytest -q`

Endpoint development commands:

```text
python endpoint_cli.py enroll --server http://127.0.0.1:8000 --token <token>
python endpoint_cli.py once
python endpoint_cli.py run --interval 20
```

The old PySide6 UI remains in the repository for reference and Windows-local reuse. It is not the primary platform architecture.
