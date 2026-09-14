"""
Punto de entrada de la aplicación.

Uso local:
    python run.py

En producción (Render, Railway, etc.), el propio hosting ejecuta la
aplicación con un servidor WSGI (gunicorn) apuntando a "run:app".
"""

import os

from dotenv import load_dotenv

load_dotenv()  # carga backend/.env si existe (solo en desarrollo local)

from app import create_app

app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=True, port=puerto)