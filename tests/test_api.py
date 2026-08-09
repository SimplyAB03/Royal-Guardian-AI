from fastapi.testclient import TestClient

from royal_guardian.api.main import app


def test_health_and_registration_flow():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        r = client.post("/api/auth/register", json={
            "email": "api@example.com",
            "password": "super-secure-password",
            "display_name": "API User",
            "organization_name": "API Co",
            "is_business": True,
        })
        assert r.status_code == 201, r.text
        me = client.get("/api/me")
        assert me.status_code == 200
        assert me.json()["tenant"]["name"] == "API Co"
        agent = client.post("/api/agents", json={"name": "Ops Guardian", "description": "Handles approved ops tasks"})
        assert agent.status_code == 201, agent.text
        agents = client.get("/api/agents").json()
        assert len(agents) == 1
