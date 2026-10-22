"""Teste sintético disponível também no executável distribuído, sem pytest."""
import tempfile
from pathlib import Path

from openpyxl import load_workbook

from app.core.catalog import discover, digest
from app.core.exporters.writer import export
from app.core.importers.reader import inspect, records, sheets
from app.core.mapping import suggest
from app.core.session import process
from app.models import Options


def synthetic_pdf(path):
    """PDF mínimo com grade, sem gerador externo nem dados reais no binário.

    Objetos/xref explícitos tornam o teste independente de reportlab. É uma
    fixture de duas colunas, não uma biblioteca de criação de documentos.
    """
    content = b"0.5 w\n50 700 m 400 700 l S\n50 670 m 400 670 l S\n50 640 m 400 640 l S\n50 640 m 50 700 l S\n180 640 m 180 700 l S\n400 640 m 400 700 l S\nBT /F1 12 Tf 60 680 Td (id_veiculo) Tj ET\nBT /F1 12 Tf 190 680 Td (descricao) Tj ET\nBT /F1 12 Tf 60 650 Td (000001) Tj ET\nBT /F1 12 Tf 190 650 Td (Veiculo sintetico) Tj ET\n"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"endstream"]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(data)


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
        pdf = folder / "sintetico.pdf"
        synthetic_pdf(pdf)
        pdf_source = inspect(pdf, sheets(pdf)[0], header_row=1)
        assert next(records(pdf_source))[1]["C1"].text == "000001"
        options.pdf_confirmed = True
        session = process(root, folder, pdf_source, layout, suggest(pdf_source, layout), options)
        try:
            assert session.stats()["read"] == 1 and session.stats()["errors"] == 0
            assert list(export([session], folder).glob("*.xlsx"))
        finally:
            session.close()
        # QtPdf is tested here because the packaged PDF viewer needs its plugin.
        from PySide6.QtPdf import QPdfDocument
        document = QPdfDocument()
        assert document.load(str(pdf)) == QPdfDocument.Error.None_
        assert document.pageCount() == 1
        document.close()
    print("SELFTEST OK: CSV/PDF, mapeamento, validação, exportação, relatório, QtPdf e zeros preservados.")
