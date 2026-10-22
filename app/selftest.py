"""Teste sintético disponível também no executável distribuído, sem pytest."""
import tempfile
from pathlib import Path

from openpyxl import load_workbook

from app.core.catalog import discover, digest
from app.core.exporters.writer import export
from app.core.importers.reader import inspect
from app.core.mapping import suggest
from app.core.session import process
from app.models import Options


def run(root, state):
    with tempfile.TemporaryDirectory(prefix="selftest-", dir=state) as directory:
        folder = Path(directory)
        layout = next(x for x in discover(root) if x.family == "veiculos")
        sourcefile = folder / "sintetico.csv"
        sourcefile.write_text("descricao;id_veiculo\nVeículo sintético;000001\n", encoding="utf-8")
        original = digest(sourcefile)
        source = inspect(sourcefile, header_row=1)
        options = Options(columns="omit", acknowledge_conflicts=True)
        session = process(root, folder, source, layout, suggest(source, layout), options)
        try:
            output = export([session], folder)
            workbook = load_workbook(next(output.glob("*.xlsx")))
            try:
                assert list(workbook.active.values) == [("id_veiculo", "descricao"), ("000001", "Veículo sintético")]
            finally:
                workbook.close()
            assert digest(sourcefile) == original
            assert (output / "relatorio.json").is_file()
        finally:
            session.close()
    print("SELFTEST OK: leitura, mapeamento, validação, exportação, relatório e zeros preservados.")
