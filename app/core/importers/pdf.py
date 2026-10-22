"""Tabelas PDF por página e geometria; texto corrido nunca vira linha de cadastro.

Cada tabela é uma fonte distinta. A confirmação visual é exigida pelo motor
antes da exportação. PDFs sem grade reconhecível ficam pendentes, sem OCR ou
inferência de campos por proximidade de texto.
"""
import re

import pdfplumber

from app.models import Cell, Control


def tables(path, control=None):
    control = control or Control()
    result = []
    with pdfplumber.open(path) as document:
        if len(document.pages) > 500:
            raise ValueError("PDF com mais de 500 páginas: separe em partes para revisão.")
        for number, page in enumerate(document.pages, 1):
            control.check()
            for index, table in enumerate(page.find_tables(), 1):
                if len(table.rows) >= 2:
                    result.append(f"Página {number} · Tabela {index}")
            page.close()
    if not result:
        raise ValueError("PDF sem tabela reconhecível. O documento continua anexado; abra o original para conferir. PDFs digitalizados exigem OCR/revisão externa.")
    return result


def rows(path, sheet, control=None):
    control = control or Control()
    match = re.fullmatch(r"Página (\d+) · Tabela (\d+)", sheet)
    if not match:
        raise ValueError("Selecione uma tabela e página válidas do PDF.")
    page_number, table_number = map(int, match.groups())
    with pdfplumber.open(path) as document:
        page = document.pages[page_number - 1]
        control.check()
        found = page.find_tables()
        table = found[table_number - 1]
        for n, row in enumerate(table.extract(), 1):
            control.check()
            yield n, [Cell(value or "", "pdf", f"Página {page_number}; tabela {table_number}; área {table.bbox}") for value in row]
