"""
Reglas de negocio del proceso: Devolución de una compra digital.

Supuestos asumidos por el equipo:
- VENTANA_DEVOLUCION_DIAS = 30: una compra solo puede devolverse dentro de los 30 días siguientes a la fecha de compra.
- Los productos de categoría marcada como no retornable (por ejemplo "perecederos") nunca son elegibles, sin importar la fecha.
- Un mismo item de compra no puede tener más de una solicitud activa o resuelta exitosamente al mismo tiempo (evita doble devolución).
"""

import secrets
import string
from datetime import datetime

from app.db import get_connection
from app.errors import (
    DatosInvalidos,
    RecursoNoEncontrado,
    SolicitudEnConflicto,
    ReglaNegocioIncumplida,
)

VENTANA_DEVOLUCION_DIAS = 30

ESTADOS_BLOQUEAN_NUEVA_SOLICITUD = (
    "pendiente_revision",
    "aprobada_automatica",
    "completada",
)

CONDICIONES_VALIDAS_PRODUCTO = ("buen_estado", "dañado", "incompleto")


def _a_datetime(valor):
    """Postgres devuelve las columnas TIMESTAMP ya como datetime; SQLite
    las devuelve como texto ISO 8601. Esta función normaliza ambos casos."""
    if isinstance(valor, str):
        return datetime.fromisoformat(valor)
    return valor


def _generar_codigo_devolucion() -> str:
    sufijo = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"DEV-{sufijo}"


def listar_compras_devolubles(cliente_id: int) -> list[dict]:
    """Devuelve las compras del cliente con cada item marcado como
    elegible o no para devolución (y el motivo si no lo es)."""
    conn = get_connection()
    try:
        cliente = conn.execute(
            "SELECT id, nombre FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        if cliente is None:
            raise RecursoNoEncontrado(
                f"No existe un cliente con id {cliente_id}.", "CLIENTE_NO_ENCONTRADO"
            )

        compras = conn.execute(
            "SELECT id, canal, fecha_compra FROM compras WHERE cliente_id = ? ORDER BY fecha_compra DESC",
            (cliente_id,),
        ).fetchall()

        resultado = []
        for compra in compras:
            items = conn.execute(
                """
                SELECT ic.id AS item_compra_id, p.nombre, p.categoria,
                       p.precio_unitario, p.es_retornable, ic.cantidad
                FROM items_compra ic
                JOIN productos p ON p.id = ic.producto_id
                WHERE ic.compra_id = ?
                """,
                (compra["id"],),
            ).fetchall()

            dias_transcurridos = (
                datetime.now() - _a_datetime(compra["fecha_compra"])
            ).days
            dentro_de_ventana = dias_transcurridos <= VENTANA_DEVOLUCION_DIAS

            items_resultado = []
            for item in items:
                solicitud_previa = conn.execute(
                    """
                    SELECT estado FROM solicitudes_devolucion
                    WHERE item_compra_id = ? AND estado IN (?, ?, ?)
                    """,
                    (item["item_compra_id"], *ESTADOS_BLOQUEAN_NUEVA_SOLICITUD),
                ).fetchone()

                elegible = True
                motivo_no_elegible = None
                if not item["es_retornable"]:
                    elegible = False
                    motivo_no_elegible = f"La categoría '{item['categoria']}' no admite devoluciones."
                elif not dentro_de_ventana:
                    elegible = False
                    motivo_no_elegible = (
                        f"La compra tiene {dias_transcurridos} días; "
                        f"supera la ventana de {VENTANA_DEVOLUCION_DIAS} días."
                    )
                elif solicitud_previa is not None:
                    elegible = False
                    motivo_no_elegible = "Este producto ya tiene una solicitud de devolución en curso."

                items_resultado.append(
                    {
                        "item_compra_id": item["item_compra_id"],
                        "producto": item["nombre"],
                        "categoria": item["categoria"],
                        "precio_unitario": item["precio_unitario"],
                        "cantidad": item["cantidad"],
                        "elegible_para_devolucion": elegible,
                        "motivo_no_elegible": motivo_no_elegible,
                    }
                )

            resultado.append(
                {
                    "compra_id": compra["id"],
                    "canal": compra["canal"],
                    "fecha_compra": compra["fecha_compra"],
                    "dias_transcurridos": dias_transcurridos,
                    "items": items_resultado,
                }
            )

        return resultado
    finally:
        conn.close()


def crear_solicitud_devolucion(item_compra_id: int, motivo_cliente: str) -> dict:
    """Valida las reglas de negocio y crea la solicitud. Si el item no
    cumple las condiciones, la solicitud igual queda registrada pero
    con estado 'rechazada_automatica' y el motivo del rechazo, para
    que quede trazabilidad de todos los intentos."""
    if not motivo_cliente or not motivo_cliente.strip():
        raise DatosInvalidos("El motivo de la devolución es obligatorio.", "MOTIVO_REQUERIDO")

    conn = get_connection()
    try:
        item = conn.execute(
            """
            SELECT ic.id AS item_compra_id, ic.compra_id, p.categoria, p.es_retornable,
                   c.fecha_compra
            FROM items_compra ic
            JOIN productos p ON p.id = ic.producto_id
            JOIN compras c ON c.id = ic.compra_id
            WHERE ic.id = ?
            """,
            (item_compra_id,),
        ).fetchone()

        if item is None:
            raise RecursoNoEncontrado(
                f"No existe el item de compra {item_compra_id}.", "ITEM_NO_ENCONTRADO"
            )

        solicitud_previa = conn.execute(
            """
            SELECT id FROM solicitudes_devolucion
            WHERE item_compra_id = ? AND estado IN (?, ?, ?)
            """,
            (item_compra_id, *ESTADOS_BLOQUEAN_NUEVA_SOLICITUD),
        ).fetchone()
        if solicitud_previa is not None:
            raise SolicitudEnConflicto(
                "Este producto ya tiene una solicitud de devolución en curso o resuelta.",
                "SOLICITUD_YA_EXISTE",
            )

        dias_transcurridos = (
            datetime.now() - _a_datetime(item["fecha_compra"])
        ).days
        dentro_de_ventana = dias_transcurridos <= VENTANA_DEVOLUCION_DIAS

        ahora = datetime.now().isoformat(timespec="seconds")
        codigo = _generar_codigo_devolucion()

        if not item["es_retornable"]:
            estado = "rechazada_automatica"
            motivo_rechazo = f"La categoría '{item['categoria']}' no admite devoluciones."
        elif not dentro_de_ventana:
            estado = "rechazada_automatica"
            motivo_rechazo = (
                f"La compra tiene {dias_transcurridos} días; "
                f"supera la ventana de {VENTANA_DEVOLUCION_DIAS} días permitidos."
            )
        else:
            estado = "aprobada_automatica"
            motivo_rechazo = None

        cur = conn.execute(
            """
            INSERT INTO solicitudes_devolucion
                (item_compra_id, codigo_devolucion, motivo_cliente, estado,
                 motivo_rechazo, fecha_solicitud, fecha_resolucion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_compra_id,
                codigo,
                motivo_cliente.strip(),
                estado,
                motivo_rechazo,
                ahora,
                ahora if estado == "rechazada_automatica" else None,
            ),
        )
        conn.commit()

        if estado == "rechazada_automatica":
            raise ReglaNegocioIncumplida(motivo_rechazo, "DEVOLUCION_NO_ELEGIBLE")

        return {
            "solicitud_id": cur.lastrowid,
            "codigo_devolucion": codigo,
            "estado": estado,
            "fecha_solicitud": ahora,
        }
    finally:
        conn.close()


def buscar_solicitud_por_codigo(codigo: str) -> dict:
    conn = get_connection()
    try:
        fila = conn.execute(
            """
            SELECT sd.*, p.nombre AS producto, p.categoria, cl.nombre AS cliente
            FROM solicitudes_devolucion sd
            JOIN items_compra ic ON ic.id = sd.item_compra_id
            JOIN productos p ON p.id = ic.producto_id
            JOIN compras c ON c.id = ic.compra_id
            JOIN clientes cl ON cl.id = c.cliente_id
            WHERE sd.codigo_devolucion = ?
            """,
            (codigo.strip().upper(),),
        ).fetchone()

        if fila is None:
            raise RecursoNoEncontrado(
                f"No existe una solicitud con el código '{codigo}'.", "CODIGO_NO_ENCONTRADO"
            )

        return dict(fila)
    finally:
        conn.close()


def registrar_revision_tienda(
    codigo: str, empleado: str, condicion_producto: str, comentario: str | None
) -> dict:
    if not empleado or not empleado.strip():
        raise DatosInvalidos("El nombre del empleado es obligatorio.", "EMPLEADO_REQUERIDO")
    if condicion_producto not in CONDICIONES_VALIDAS_PRODUCTO:
        raise DatosInvalidos(
            f"condicion_producto debe ser una de: {', '.join(CONDICIONES_VALIDAS_PRODUCTO)}.",
            "CONDICION_INVALIDA",
        )

    conn = get_connection()
    try:
        solicitud = conn.execute(
            "SELECT * FROM solicitudes_devolucion WHERE codigo_devolucion = ?",
            (codigo.strip().upper(),),
        ).fetchone()

        if solicitud is None:
            raise RecursoNoEncontrado(
                f"No existe una solicitud con el código '{codigo}'.", "CODIGO_NO_ENCONTRADO"
            )

        if solicitud["estado"] != "aprobada_automatica":
            raise SolicitudEnConflicto(
                f"La solicitud ya fue procesada (estado actual: {solicitud['estado']}).",
                "SOLICITUD_YA_PROCESADA",
            )

        ahora = datetime.now().isoformat(timespec="seconds")
        nuevo_estado = "completada" if condicion_producto == "buen_estado" else "rechazada_tienda"
        motivo_rechazo = None
        if nuevo_estado == "rechazada_tienda":
            motivo_rechazo = f"Producto recibido en estado '{condicion_producto}' según revisión en tienda."

        conn.execute(
            """
            INSERT INTO revisiones_tienda
                (solicitud_id, empleado, condicion_producto, comentario, fecha_revision)
            VALUES (?, ?, ?, ?, ?)
            """,
            (solicitud["id"], empleado.strip(), condicion_producto, comentario, ahora),
        )
        conn.execute(
            """
            UPDATE solicitudes_devolucion
            SET estado = ?, motivo_rechazo = ?, fecha_resolucion = ?
            WHERE id = ?
            """,
            (nuevo_estado, motivo_rechazo, ahora, solicitud["id"]),
        )
        conn.commit()

        return {
            "codigo_devolucion": solicitud["codigo_devolucion"],
            "estado": nuevo_estado,
            "motivo_rechazo": motivo_rechazo,
            "fecha_resolucion": ahora,
        }
    finally:
        conn.close()


def listar_solicitudes_cliente(cliente_id: int) -> list[dict]:
    conn = get_connection()
    try:
        cliente = conn.execute(
            "SELECT id FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        if cliente is None:
            raise RecursoNoEncontrado(
                f"No existe un cliente con id {cliente_id}.", "CLIENTE_NO_ENCONTRADO"
            )

        filas = conn.execute(
            """
            SELECT sd.codigo_devolucion, sd.estado, sd.motivo_cliente, sd.motivo_rechazo,
                   sd.fecha_solicitud, sd.fecha_resolucion, p.nombre AS producto
            FROM solicitudes_devolucion sd
            JOIN items_compra ic ON ic.id = sd.item_compra_id
            JOIN productos p ON p.id = ic.producto_id
            JOIN compras c ON c.id = ic.compra_id
            WHERE c.cliente_id = ?
            ORDER BY sd.fecha_solicitud DESC
            """,
            (cliente_id,),
        ).fetchall()

        return [dict(f) for f in filas]
    finally:
        conn.close()