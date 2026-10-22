from pathlib import Path

import pytest
from openpyxl import Workbook

from app.core.catalog import discover
from app.core.importers.reader import inspect
from app.core.mapping import suggest
from app.core.session import process
from app.models import Options

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def layouts():
    return discover(ROOT)


@pytest.fixture
def layout(layouts):
    return lambda family, variant="record": next(x for x in layouts if x.family == family and x.variant == variant and x.path.parent.name == "V1")


@pytest.fixture
def make_xlsx(tmp_path):
    def make(headers, rows, name="sintetico.xlsx"):
        book = Workbook()
        sheet = book.active
        sheet.title = "Dados"
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        path = tmp_path / name
        book.save(path)
        book.close()
        return path
    return make


@pytest.fixture
def options():
    return Options(active="no", columns="omit", acknowledge_conflicts=True, geography_confirmed=True, geography_evidence="Dados sintéticos de teste: localidade/UF conferidos.")


@pytest.fixture
def convert(tmp_path, make_xlsx, options):
    sessions = []
    def run(layout, headers, rows, opts=None, name="sintetico.xlsx"):
        path = make_xlsx(headers, rows, name)
        source = inspect(path, header_row=1)
        mapping = suggest(source, layout)
        for d in mapping:
            if d.target:
                d.confirmed = True
        session = process(ROOT, tmp_path, source, layout, mapping, opts or options)
        sessions.append(session)
        return session
    yield run
    for session in sessions:
        session.close()


def synthetic_cpf():
    base = "000000001"
    for _ in range(2):
        rem = sum(int(v) * w for v, w in zip(base, range(len(base)+1, 1, -1))) % 11
        base += str(0 if rem < 2 else 11-rem)
    return base
