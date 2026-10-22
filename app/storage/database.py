"""Transação com fechamento determinístico, inclusive em erro e no Windows.

O context manager de sqlite3.Connection faz commit/rollback, mas não fecha a
conexão. closing externo evita deixar handles dependentes do coletor de lixo.
"""
import sqlite3
from contextlib import closing, contextmanager


@contextmanager
def database(path):
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            yield connection
