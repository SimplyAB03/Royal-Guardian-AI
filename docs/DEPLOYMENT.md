# Deployment

## Local development
1. Create a Python 3.11+ virtual environment.
2. Install `requirements.txt`.
3. Copy `.env.example` values into environment variables (the app does not automatically load `.env`).
4. Set a non-default `RG_SESSION_SECRET`.
5. Run `python run_server.py`.
6. Open `http://127.0.0.1:8000`.

## Production target
- Managed PostgreSQL.
- HTTPS behind a reverse proxy/load balancer.
- Managed secrets/KMS for provider credentials.
- Persistent worker/queue for workflows and scheduled jobs.
- Object storage for uploads and endpoint update artifacts.
- Central logs/error tracking/metrics.
- Separate signed Windows build pipeline.

Do not use the development SQLite configuration for a real multi-instance production service.
