"""
Configuración compartida de las pruebas.

Cada prueba recibe un cliente de Flask (`client`) conectado a una
base de datos SQLite recién poblada con los datos de seed.py, para
que las pruebas sean reproducibles y no dependan de datos previos.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import pytest
import seed  # noqa: E402  (backend/seed.py)
from app import create_app  # noqa: E402


@pytest.fixture()
def client():
    seed.main()  # recrea y puebla la base de datos antes de cada prueba
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client