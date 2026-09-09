"""
Capa de conexión a la base de datos.

Soporta dos backends:

- No está definida  →  usa SQLite local (mercado_viva.db).
- Definida con una cadena de Postgres →  usa Postgres en la nube.
"""

import os
import re
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")

BACKEND_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BACKEND_DIR / "mercado_viva.db"
SCHEMA_SQLITE_PATH = BACKEND_DIR / "schema.sql"
SCHEMA_POSTGRES_PATH = BACKEND_DIR / "schema_postgres.sql"

_PLACEHOLDER_RE = re.compile(r"\?")


class _CursorPostgres:
    """Envuelve un cursor de psycopg2 para que se comporte, en lo que el
    resto del código usa, igual que un cursor de sqlite3: placeholders
    '?' y un atributo .lastrowid disponible tras un INSERT."""

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql_pg = _PLACEHOLDER_RE.sub("%s", sql)
        es_insert = sql_pg.strip().upper().startswith("INSERT")
        if es_insert and "RETURNING" not in sql_pg.upper():
            sql_pg += " RETURNING id"
        self._cursor.execute(sql_pg, params)
        if es_insert:
            fila = self._cursor.fetchone()
            self.lastrowid = fila["id"] if fila else None
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class ConexionPostgres:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        return _CursorPostgres(self._conn.cursor()).execute(sql, params)

    def executescript(self, sql):
        cur = self._conn.cursor()
        cur.execute(sql)
        self._conn.commit()

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_connection():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode="require",
        )
        return ConexionPostgres(conn)

    import sqlite3

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn