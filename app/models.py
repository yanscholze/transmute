"""Contratos compartilhados: não dependem de Qt, HTTP ou armazenamento."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


class Cancelled(Exception):
    pass


@dataclass
class Control:
    cancelled: Callable[[], bool] = lambda: False
    progress: Callable[[int, str], None] = lambda n, message: None

    def check(self):
        if self.cancelled():
            raise Cancelled("Operação cancelada; nenhum arquivo de importação foi publicado.")


@dataclass
class Cell:
    text: str = ""
    kind: str = "text"
    note: str = ""


@dataclass
class Source:
    path: Path
    sheet: str
    header_row: int
    headers: list[str]
    encoding: str = ""
    delimiter: str = ""
    format: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def ids(self):
        return [f"C{i + 1}" for i in range(len(self.headers))]


@dataclass
class Layout:
    path: Path
    sheet: str
    headers: list[str]
    family: str
    variant: str
    digest: str

    @property
    def label(self):
        names = {"clientes": "Clientes", "fornecedores": "Fornecedores", "produtos": "Produtos",
                 "veiculos": "Veículos", "pagar": "Contas a pagar", "receber": "Contas a receber",
                 "os": "Ordens de serviço", "vendas": "Vendas", "generic": self.path.stem}
        suffix = {"header": " · cabeçalhos", "items": " · itens", "joined": " · juntos"}.get(self.variant, "")
        return f"{self.path.parent.name} · {names[self.family]}{suffix}"


@dataclass
class Decision:
    source: str
    target: str
    confidence: float
    origin: str
    confirmed: bool = False
    reason: str = ""


@dataclass
class Issue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class Change:
    field: str
    before: str
    after: str
    rule: str


@dataclass
class Options:
    active: str = ""  # yes / no: decisão explícita por conversão
    columns: str = ""  # omit / full: conflito explicitado
    acknowledge_conflicts: bool = False
    geography_confirmed: bool = False
    geography_evidence: str = ""
    oil_cfop_evidence: str = ""
    numeric_identifiers_confirmed: bool = False
    partial: bool = False
    overrides: dict = field(default_factory=dict)
