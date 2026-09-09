"""
Fábrica de la aplicación Flask — Módulo de Devoluciones Digitales.
"""

from pathlib import Path

from flask import Flask, send_from_directory

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def create_app() -> Flask:
    app = Flask(__name__)

    from app.routes.devoluciones_routes import bp as devoluciones_bp

    app.register_blueprint(devoluciones_bp)

    # Sirve el frontend estático (HTML/CSS/JS) directamente desde Flask,
    # para que el proyecto se pueda ejecutar con un solo comando.
    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "cliente.html")

    @app.get("/tienda")
    def tienda():
        return send_from_directory(FRONTEND_DIR, "tienda.html")

    @app.get("/css/<path:nombre_archivo>")
    def css(nombre_archivo):
        return send_from_directory(FRONTEND_DIR / "css", nombre_archivo)

    @app.get("/js/<path:nombre_archivo>")
    def js(nombre_archivo):
        return send_from_directory(FRONTEND_DIR / "js", nombre_archivo)

    return app