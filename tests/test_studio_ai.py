"""Full planning/audit contracts over mocked HTTP; no paid calls or real data."""
import json

import httpx
import pytest

from app.ai.configuration import configured_providers, readiness
from app.ai.credentials import Credentials
from app.ai.providers import APIProvider
from app.ai.studio import planning_payload, request_audit, request_plan
from app.studio.catalog import inventory
from tests.test_studio import library, project, recipe, route


@pytest.mark.parametrize("provider", ["OpenAI", "Gemini", "Claude"])
def test_each_provider_can_plan_and_audit_through_http(provider, tmp_path, make_xlsx, options):
    root = library(tmp_path, make_xlsx, [("destino.xlsx", ["Nome"], "generic")])
    job = project(tmp_path, [make_xlsx(["Nome"], [["Pessoa privada sintética"]])], options)
    context = inventory(root, job)
    plan = recipe([route(context, "out", "destino.xlsx", 0, {"Nome": "C1"})])
    payload = planning_payload(context, "# Regras sintéticas", headers=True)
    assert "Pessoa privada" not in json.dumps(payload, ensure_ascii=False)
    assert "path" not in payload["sources"][0]
    requests, responses = [], [plan, {"summary": "Auditoria sintética", "findings": [], "questions": []}]
    def mock(request):
        requests.append(request)
        body = json.loads(request.content)
        result = responses.pop(0)
        if provider == "OpenAI":
            assert body["store"] is False and body["text"]["format"]["strict"] is True
            assert "tools" not in body
            response = {"output": [{"content": [{"type": "output_text", "text": json.dumps(result)}]}]}
        elif provider == "Gemini":
            assert request.headers["x-goog-api-key"] == "synthetic-key"
            assert "synthetic-key" not in str(request.url)
            assert body["generationConfig"]["responseJsonSchema"]["additionalProperties"] is False
            response = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(result)}]}}]}
        else:
            assert request.headers["anthropic-version"] == "2023-06-01"
            assert body["tool_choice"]["name"] == "conversion_result"
            response = {"content": [{"type": "tool_use", "name": "conversion_result", "input": result}]}
        return httpx.Response(200, json=response)
    client = APIProvider(provider, "synthetic-model", "synthetic-key", transport=httpx.MockTransport(mock))
    result, event = request_plan([client], payload, context)
    assert result == plan and event["provider"] == provider
    result, _ = request_audit([client], {"plan": plan})
    assert result["summary"] == "Auditoria sintética" and len(requests) == 2


def test_providers_use_independent_environment_credentials_and_models(tmp_path, monkeypatch):
    import keyring
    monkeypatch.setattr(keyring, "get_keyring", lambda: object())
    env = {"OPENAI_API_KEY": "synthetic-openai", "GEMINI_API_KEY": "synthetic-gemini", "ANTHROPIC_API_KEY": "synthetic-claude",
           "OPENAI_MODEL": "openai-synthetic", "GEMINI_MODEL": "gemini-synthetic", "ANTHROPIC_MODEL": "claude-synthetic"}
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    credentials = Credentials()
    assert credentials.get("OpenAI") == env["OPENAI_API_KEY"]
    assert credentials.get("Gemini") == env["GEMINI_API_KEY"]
    assert credentials.get("Claude") == env["ANTHROPIC_API_KEY"]
    import app.ai.configuration as configuration
    monkeypatch.setattr(configuration, "credentials", credentials)
    config = {"provider": "OpenAI", "fallback": ["Gemini", "Claude"], "models": {}}
    clients = configured_providers(config, tmp_path)
    assert [c.model for c in clients] == ["openai-synthetic", "gemini-synthetic", "claude-synthetic"]
    assert all(r["model"] and r["credential"] for r in readiness(config))
    assert all("key" not in key and "secret" not in key for row in readiness(config) for key in row)


def test_invalid_or_interrupted_provider_output_never_becomes_a_plan(tmp_path, make_xlsx, options):
    root = library(tmp_path, make_xlsx, [("destino.xlsx", ["Nome"], "generic")])
    job = project(tmp_path, [make_xlsx(["Nome"], [["Sintético"]])], options)
    context = inventory(root, job)
    class Unsafe:
        name, model = "Gemini", "synthetic"
        def generate(self, *args):
            return '{"command":"delete"}'
    with pytest.raises(ValueError, match="Nenhum provedor"):
        request_plan([Unsafe()], {}, context)
    provider = APIProvider("Gemini", "synthetic", "synthetic-key")
    with pytest.raises(ValueError, match="interrompida"):
        provider.extract({"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": []}}]})
    provider.name = "Claude"
    with pytest.raises(ValueError, match="incompleta"):
        provider.extract({"stop_reason": "max_tokens", "content": []})


def test_development_env_is_read_only_whitelisted_and_never_executed(tmp_path, monkeypatch):
    from app.ai.environment import load_development_env
    for name in ["GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_MODEL"]:
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-existing")
    path = tmp_path / ".env.local"
    content = 'GEMINI_API_KEY="synthetic-google"\nANTHROPIC_API_KEY=synthetic-claude\nOPENAI_API_KEY=synthetic-replacement\nGEMINI_MODEL=synthetic-model\nUNRELATED_ENV=do-not-load\n'
    path.write_text(content)
    load_development_env(tmp_path)
    import os
    assert os.environ["OPENAI_API_KEY"] == "synthetic-existing"
    assert os.environ["GEMINI_API_KEY"] == "synthetic-google"
    assert os.environ["ANTHROPIC_API_KEY"] == "synthetic-claude"
    assert "UNRELATED_ENV" not in os.environ
    assert path.read_text() == content
