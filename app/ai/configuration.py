"""Provider configuration independent of widgets; models and keys stay separate."""
import os
import re

from app.ai.cli import CLIProvider
from app.ai.credentials import credentials
from app.ai.providers import APIProvider

PROVIDERS = ("OpenAI", "Gemini", "Claude", "Claude CLI")
MODEL_ENV = {"OpenAI": "OPENAI_MODEL", "Gemini": "GEMINI_MODEL", "Claude": "ANTHROPIC_MODEL"}


def model_for(config, name):
    return config.get("models", {}).get(name, "").strip() or os.environ.get(MODEL_ENV.get(name, ""), "").strip()


def configured_providers(config, state):
    names = [config.get("provider", "OpenAI")] + config.get("fallback", [])
    if any(name not in PROVIDERS for name in names) or len(set(names)) != len(names):
        raise ValueError("Selecione provedores distintos e válidos.")
    providers = []
    for name in names:
        model = model_for(config, name)
        if model and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}", model):
            raise ValueError("Nome do modelo contém caracteres inválidos.")
        if name == "Claude CLI":
            providers.append(CLIProvider(state / "cli", model, config.get("timeout", 60)))
        else:
            providers.append(APIProvider(name, model, credentials.get(name), config.get("timeout", 60)))
    return providers


def readiness(config):
    """Presence is reported separately from an actual successful network test."""
    return [{"provider": name, "model": bool(model_for(config, name)), "credential": bool(credentials.get(name))}
            for name in PROVIDERS if name != "Claude CLI"]
