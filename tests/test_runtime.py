from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from royal_guardian.db.base import Base
from royal_guardian.db.models import Agent, AgentRun, Device, DeviceStatus
import royal_guardian.services.runtime as runtime
from royal_guardian.services.ai import AIResult, ToolCall

class FakeProvider:
    def __init__(self): self.calls=0
    def generate(self, **kwargs):
        self.calls+=1
        if self.calls==1:
            return AIResult('', 'fake','fake',{},[ToolCall('1','list_devices',{})])
        return AIResult('I verified the registered device list.', 'fake','fake',{})

def test_agent_runtime_uses_registered_read_only_tool(monkeypatch):
    eng=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(eng); S=sessionmaker(bind=eng,expire_on_commit=False); db=S()
    agent=Agent(tenant_id='t1',owner_id='u1',name='IT Guardian',model_provider='anthropic',model_name='x',tools=['list_devices'])
    db.add(agent); db.flush()
    db.add(Device(tenant_id='t1',name='PC-1',fingerprint='fingerprint1',auth_token_hash='hash',status=DeviceStatus.ONLINE))
    run=AgentRun(tenant_id='t1',agent_id=agent.id,user_id='u1',input_text='show devices')
    db.add(run); db.flush()
    fake=FakeProvider(); monkeypatch.setattr(runtime,'get_provider',lambda _: fake)
    result=runtime.run_agent_runtime(db,agent=agent,run=run,user_id='u1',message='show devices')
    assert 'verified' in result['text']
    assert fake.calls==2
