"""Detecção conservadora de CLI e execução só com controles confirmados.

Comandos são listas fixas, sem shell. Claude roda sem ferramentas/MCP e em
diretório vazio; Codex/Gemini permanecem detectáveis sem execução habilitada.
"""
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass

from app.ai.providers import SYSTEM
from app.models import Control

REQUIRED_CLAUDE = ["--tools", "--strict-mcp-config", "--mcp-config", "--safe-mode", "--no-session-persistence", "--disable-slash-commands", "--json-schema", "--output-format"]


def detect_clis(control=None):
    control = control or Control()
    result = []
    for name in ["codex", "gemini", "claude"]:
        control.check()
        path = shutil.which(name)
        available, enabled = bool(path), False
        reason = "Não instalado."
        if path:
            try:
                run = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=10, shell=False)
                help_text = run.stdout + run.stderr
                if name == "claude":
                    enabled = run.returncode == 0 and all(flag in help_text for flag in REQUIRED_CLAUDE)
                    reason = "Modo sem ferramentas e sem persistência confirmado no --help; autenticação ainda não testada." if enabled else "Versão não confirma todos os controles de isolamento necessários."
                else:
                    reason = "Detectado. Execução desabilitada: não foi confirmado um contrato sem ferramentas/hooks para esta versão."
            except (OSError, subprocess.SubprocessError):
                reason = "Executável encontrado, mas a inspeção --help falhou."
        result.append({"name": name, "path": path or "", "available": available, "enabled": enabled, "reason": reason})
    return result


@dataclass
class CLIProvider:
    directory: object
    model: str = ""
    timeout: int = 30
    name: str = "Claude CLI"

    def generate(self, data, output_schema, control=None):
        control = control or Control()
        found = next(x for x in detect_clis(control) if x["name"] == "claude")
        if not found["enabled"]:
            raise ValueError(found["reason"])
        args = [found["path"], "-p", "--safe-mode", "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence", "--disable-slash-commands", "--output-format", "json", "--json-schema", json.dumps(output_schema), "--system-prompt", SYSTEM]
        if self.model:
            args += ["--model", self.model]
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(prefix="cli-", dir=self.directory) as cwd:
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", cwd=cwd, shell=False, start_new_session=os.name != "nt")
            try:
                process.stdin.write(json.dumps({"untrusted_data": data}, ensure_ascii=False))
                process.stdin.close()
                process.stdin = None
                start = time.monotonic()
                while True:
                    control.check()
                    if time.monotonic() - start > self.timeout:
                        raise ValueError("CLI excedeu o timeout configurado.")
                    try:
                        stdout, _ = process.communicate(timeout=.15)
                        break
                    except subprocess.TimeoutExpired:
                        continue
                if process.returncode != 0 or len(stdout) > 1024 * 1024:
                    raise ValueError("CLI falhou; autentique-a separadamente no terminal. Nenhum stderr contendo dados foi registrado.")
                data = json.loads(stdout)
                if data.get("is_error"):
                    raise ValueError("CLI retornou erro de autenticação ou execução.")
                structured = data.get("structured_output", data.get("result", data))
                return structured if isinstance(structured, str) else json.dumps(structured, ensure_ascii=False)
            finally:
                if process.poll() is None:
                    if os.name != "nt":
                        os.killpg(process.pid, signal.SIGTERM)
                    else:
                        process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        if os.name != "nt":
                            os.killpg(process.pid, signal.SIGKILL)
                        else:
                            process.kill()
                        process.wait()
