from fastapi.testclient import TestClient
from royal_guardian.api.main import app


def _register(client, email):
    r=client.post('/api/auth/register',json={'email':email,'password':'super-secure-password','display_name':'Tester'})
    assert r.status_code==201, r.text


def test_knowledge_memory_workflow_and_billing_free():
    with TestClient(app) as c:
        _register(c,'phase2@example.com')
        a=c.post('/api/agents',json={'name':'Research Guardian'}).json()
        r=c.post('/api/knowledge',json={'agent_id':a['id'],'name':'Policy','content':'Royal Guardian requires human approval for risky actions.'})
        assert r.status_code==201
        assert c.get('/api/knowledge').json()[0]['name']=='Policy'
        m=c.post('/api/memory',json={'agent_id':a['id'],'scope':'agent','key':'tone','content':'Use concise responses.'})
        assert m.status_code==201
        assert c.get('/api/memory',params={'agent_id':a['id']}).status_code==200
        w=c.post('/api/workflows',json={'agent_id':a['id'],'name':'Morning brief','trigger_type':'schedule','definition':{'steps':[]}})
        assert w.status_code==201
        assert c.get('/api/workflows').json()[0]['name']=='Morning brief'
        b=c.get('/api/billing').json()
        assert b['plan']=='free' and b['entitlements']['max_agents']==1


def test_oauth_start_truthfully_blocks_without_credentials(monkeypatch):
    monkeypatch.delenv('GOOGLE_CLIENT_ID',raising=False)
    with TestClient(app) as c:
        _register(c,'oauth@example.com')
        r=c.get('/api/oauth/google/start')
        assert r.status_code==503
        assert 'GOOGLE_CLIENT_ID' in r.json()['detail']
