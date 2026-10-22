"""Gera índice auditável de todos os símbolos Python sem importar o aplicativo."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lines = ["# Índice do código", "", "Gerado por `scripts/document_code.py`. A árvore e os contratos são explicados em DESENVOLVIMENTO.md. Números de linha ajudam a localizar os pontos de extensão.", ""]
for base in ["app", "scripts", "tests"]:
    for path in sorted((ROOT / base).rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not tree.body:
            continue
        rel = path.relative_to(ROOT)
        lines += [f"## {rel}", "", ast.get_docstring(tree) or "Módulo da camada " + str(path.parent.relative_to(ROOT)) + ".", ""]
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node) or ""
                lines.append(f"- `{node.name}` (linha {node.lineno})" + (": " + doc.splitlines()[0] if doc else ""))
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    if methods:
                        lines.append("  Métodos: " + ", ".join(f"`{n.name}`:{n.lineno}" for n in methods) + ".")
        lines.append("")
(ROOT / "docs/CODIGO.md").write_text("\n".join(lines), encoding="utf-8")
print("docs/CODIGO.md atualizado.")
