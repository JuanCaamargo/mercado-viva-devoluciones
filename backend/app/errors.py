"""
Excepciones de dominio.

Cada una se traduce a un código HTTP específico en las rutas,
para que el frontend pueda distinguir el tipo de error y mostrar
un mensaje adecuado al usuario.
"""


class ErrorDominio(Exception):
    codigo_http = 400

    def __init__(self, mensaje: str, codigo_error: str):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_error = codigo_error


class DatosInvalidos(ErrorDominio):
    """Faltan campos obligatorios o vienen en un formato incorrecto."""
    codigo_http = 400


class RecursoNoEncontrado(ErrorDominio):
    """La compra, el item o el código de devolución no existen."""
    codigo_http = 404


class SolicitudEnConflicto(ErrorDominio):
    """El item ya tiene una solicitud de devolución en curso o resuelta."""
    codigo_http = 409


class ReglaNegocioIncumplida(ErrorDominio):
    """La compra no cumple las condiciones para devolverse (ventana, categoría, etc.)."""
    codigo_http = 422