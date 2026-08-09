from __future__ import annotations
import json, os, urllib.error, urllib.request
from dataclasses import dataclass, field

class AIProviderError(RuntimeError): pass

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

@dataclass
class AIResult:
    text: str
    provider: str
    model: str
    usage: dict
    tool_calls: list[ToolCall] = field(default_factory=list)

class AIProvider:
    id="base"
    def generate(self, *, model:str, system:str, messages:list[dict], max_tokens:int=1024, tools:list[dict]|None=None)->AIResult: raise NotImplementedError
    @staticmethod
    def _post(url:str, headers:dict[str,str], payload:dict)->dict:
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json",**headers},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=60) as resp: return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail=exc.read().decode(errors="replace")[:2000]; raise AIProviderError(f"Provider HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc: raise AIProviderError(f"Provider unavailable: {exc.reason}") from exc

class AnthropicProvider(AIProvider):
    id="anthropic"
    def __init__(self): self.api_key=os.getenv("ANTHROPIC_API_KEY","")
    def generate(self, *, model:str, system:str, messages:list[dict], max_tokens:int=1024, tools:list[dict]|None=None)->AIResult:
        if not self.api_key: raise AIProviderError("ANTHROPIC_API_KEY is not configured")
        if not model: raise AIProviderError("An Anthropic model name must be configured for this agent")
        payload={"model":model,"max_tokens":max_tokens,"system":system,"messages":messages}
        if tools:
            payload["tools"]=[{"name":t["name"],"description":t.get("description",t["name"]),"input_schema":t.get("input_schema",{"type":"object","properties":{}})} for t in tools]
        data=self._post("https://api.anthropic.com/v1/messages",{"x-api-key":self.api_key,"anthropic-version":"2023-06-01"},payload)
        text=""; calls=[]
        for part in data.get("content",[]):
            if part.get("type")=="text": text+=part.get("text","")
            elif part.get("type")=="tool_use": calls.append(ToolCall(part.get("id",""),part.get("name",""),part.get("input") or {}))
        return AIResult(text,self.id,model,data.get("usage",{}),calls)

class OpenAIProvider(AIProvider):
    id="openai"
    def __init__(self): self.api_key=os.getenv("OPENAI_API_KEY","")
    def generate(self, *, model:str, system:str, messages:list[dict], max_tokens:int=1024, tools:list[dict]|None=None)->AIResult:
        if not self.api_key: raise AIProviderError("OPENAI_API_KEY is not configured")
        if not model: raise AIProviderError("An OpenAI model name must be configured for this agent")
        payload={"model":model,"messages":[{"role":"system","content":system},*messages],"max_completion_tokens":max_tokens}
        if tools:
            payload["tools"]=[{"type":"function","function":{"name":t["name"],"description":t.get("description",t["name"]),"parameters":t.get("input_schema",{"type":"object","properties":{}})}} for t in tools]
        data=self._post("https://api.openai.com/v1/chat/completions",{"Authorization":f"Bearer {self.api_key}"},payload)
        msg=data.get("choices",[{}])[0].get("message",{})
        calls=[]
        for c in msg.get("tool_calls",[]) or []:
            f=c.get("function",{}); raw=f.get("arguments","{}")
            try: args=json.loads(raw)
            except json.JSONDecodeError: args={}
            calls.append(ToolCall(c.get("id",""),f.get("name",""),args))
        return AIResult(msg.get("content") or "",self.id,model,data.get("usage",{}),calls)

class GeminiProvider(AIProvider):
    id="gemini"
    def __init__(self): self.api_key=os.getenv("GOOGLE_AI_API_KEY","")
    def generate(self, *, model:str, system:str, messages:list[dict], max_tokens:int=1024, tools:list[dict]|None=None)->AIResult:
        if not self.api_key: raise AIProviderError("GOOGLE_AI_API_KEY is not configured")
        if not model: raise AIProviderError("A Gemini model name must be configured for this agent")
        contents=[]
        for m in messages:
            role="user" if m.get("role")=="user" else "model"
            content=m.get("content","")
            contents.append({"role":role,"parts":[{"text":content if isinstance(content,str) else json.dumps(content)}]})
        payload={"systemInstruction":{"parts":[{"text":system}]},"contents":contents,"generationConfig":{"maxOutputTokens":max_tokens}}
        if tools:
            payload["tools"]=[{"functionDeclarations":[{"name":t["name"],"description":t.get("description",t["name"]),"parameters":t.get("input_schema",{"type":"object","properties":{}})} for t in tools]}]
        data=self._post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",{},payload)
        candidates=data.get("candidates",[]); parts=candidates[0].get("content",{}).get("parts",[]) if candidates else []
        text=""; calls=[]
        for i,p in enumerate(parts):
            if "text" in p: text+=p.get("text","")
            if "functionCall" in p:
                f=p["functionCall"]; calls.append(ToolCall(f"gemini-{i}",f.get("name",""),f.get("args") or {}))
        return AIResult(text,self.id,model,data.get("usageMetadata",{}),calls)

PROVIDERS={"anthropic":AnthropicProvider,"openai":OpenAIProvider,"gemini":GeminiProvider}
def get_provider(provider_id:str)->AIProvider:
    p=PROVIDERS.get(provider_id)
    if not p: raise AIProviderError(f"Unsupported AI provider: {provider_id}")
    return p()
