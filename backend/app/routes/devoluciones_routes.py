"""
Endpoints REST del proceso de devolución de una compra digital.

Prefijo: /api
"""

from flask import Blueprint, jsonify, request

from app.errors import ErrorDominio
from app.services import devoluciones_service as servicio

bp = Blueprint("devoluciones", __name__, url_prefix="/api")


@bp.errorhandler(ErrorDominio)
def manejar_error_dominio(error: ErrorDominio):
    return (
        jsonify({"error": True, "codigo_error": error.codigo_error, "mensaje": error.mensaje}),
        error.codigo_http,
    )


@bp.get("/clientes/<int:cliente_id>/compras")
def obtener_compras_devolubles(cliente_id: int):
    compras = servicio.listar_compras_devolubles(cliente_id)
    return jsonify({"cliente_id": cliente_id, "compras": compras})


@bp.post("/devoluciones")
def crear_devolucion():
    cuerpo = request.get_json(silent=True) or {}
    item_compra_id = cuerpo.get("item_compra_id")
    motivo_cliente = cuerpo.get("motivo_cliente", "")

    if item_compra_id is None:
        return (
            jsonify(
                {
                    "error": True,
                    "codigo_error": "ITEM_COMPRA_ID_REQUERIDO",
                    "mensaje": "item_compra_id es obligatorio.",
                }
            ),
            400,
        )

    resultado = servicio.crear_solicitud_devolucion(int(item_compra_id), motivo_cliente)
    return jsonify(resultado), 201


@bp.get("/devoluciones/codigo/<string:codigo>")
def consultar_devolucion_por_codigo(codigo: str):
    solicitud = servicio.buscar_solicitud_por_codigo(codigo)
    return jsonify(solicitud)


@bp.post("/devoluciones/codigo/<string:codigo>/revision")
def revisar_producto_en_tienda(codigo: str):
    cuerpo = request.get_json(silent=True) or {}
    empleado = cuerpo.get("empleado", "")
    condicion_producto = cuerpo.get("condicion_producto", "")
    comentario = cuerpo.get("comentario")

    resultado = servicio.registrar_revision_tienda(codigo, empleado, condicion_producto, comentario)
    return jsonify(resultado)


@bp.get("/clientes/<int:cliente_id>/devoluciones")
def obtener_devoluciones_cliente(cliente_id: int):
    solicitudes = servicio.listar_solicitudes_cliente(cliente_id)
    return jsonify({"cliente_id": cliente_id, "solicitudes": solicitudes})