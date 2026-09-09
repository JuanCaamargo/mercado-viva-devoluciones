"""
Punto de entrada de la aplicación.

Uso local:
    python run.py

En producción (Render, Railway, etc.), el propio hosting ejecuta la
aplicación con un servidor WSGI (gunicorn) apuntando a "run:app",
así que el bloque de abajo solo se usa en desarrollo local.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=True, port=puerto)