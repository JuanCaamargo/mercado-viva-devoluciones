"""
Poblado de datos de ejemplo para el Módulo de Devoluciones Digitales.

Crea (o recrea) las tablas a partir del esquema correspondiente (SQLite o
Postgres, según DATABASE_URL) y las llena con clientes, productos, compras
e items de ejemplo, listos para probar el flujo completo de devolución.
"""

from datetime import datetime, timedelta

from app.db import get_connection, USE_POSTGRES, SCHEMA_SQLITE_PATH, SCHEMA_POSTGRES_PATH


def hace_dias(dias: int) -> str:
    return (datetime.now() - timedelta(days=dias)).isoformat(timespec="seconds")


def main():
    conn = get_connection()

    schema_path = SCHEMA_POSTGRES_PATH if USE_POSTGRES else SCHEMA_SQLITE_PATH
    conn.executescript(schema_path.read_text(encoding="utf-8"))

    # --- Clientes ---
    for nombre, correo in [
        ("Laura Gómez", "laura.gomez@correo.com"),
        ("Andrés Ruiz", "andres.ruiz@correo.com"),
    ]:
        conn.execute(
            "INSERT INTO clientes (nombre, correo) VALUES (?, ?)", (nombre, correo)
        )

    # --- Productos (algunos retornables, otros no por categoría) ---
    productos = [
        ("Licuadora Vivax 600W", "electrodomésticos", 189000, 1),
        ("Audífonos inalámbricos SonoPlus", "tecnología", 129000, 1),
        ("Leche entera x 1L", "perecederos", 4200, 0),   # no retornable
        ("Set de sartenes antiadherentes", "hogar", 156000, 1),
        ("Aguacate Hass x kg", "perecederos", 6800, 0),  # no retornable
    ]
    for nombre, categoria, precio, retornable in productos:
        conn.execute(
            "INSERT INTO productos (nombre, categoria, precio_unitario, es_retornable) VALUES (?, ?, ?, ?)",
            (nombre, categoria, precio, retornable),
        )

    # --- Compras ---
    # Compra 1 (cliente 1): dentro de la ventana de devolución (10 días)
    cur = conn.execute(
        "INSERT INTO compras (cliente_id, canal, fecha_compra) VALUES (?, ?, ?)",
        (1, "app", hace_dias(10)),
    )
    compra_1 = cur.lastrowid

    # Compra 2 (cliente 1): fuera de la ventana de devolución (45 días) -> caso excepcional
    cur = conn.execute(
        "INSERT INTO compras (cliente_id, canal, fecha_compra) VALUES (?, ?, ?)",
        (1, "web", hace_dias(45)),
    )
    compra_2 = cur.lastrowid

    # Compra 3 (cliente 2): incluye productos no retornables (perecederos)
    cur = conn.execute(
        "INSERT INTO compras (cliente_id, canal, fecha_compra) VALUES (?, ?, ?)",
        (2, "app", hace_dias(3)),
    )
    compra_3 = cur.lastrowid

    # --- Items de compra ---
    items = [
        (compra_1, 1, 1),  # Licuadora - elegible
        (compra_1, 2, 1),  # Audífonos - elegible
        (compra_2, 4, 1),  # Set de sartenes - fuera de ventana
        (compra_3, 3, 2),  # Leche - no retornable por categoría
        (compra_3, 5, 3),  # Aguacate - no retornable por categoría
    ]
    for compra_id, producto_id, cantidad in items:
        conn.execute(
            "INSERT INTO items_compra (compra_id, producto_id, cantidad) VALUES (?, ?, ?)",
            (compra_id, producto_id, cantidad),
        )

    conn.commit()
    conn.close()
    print(f"Base de datos poblada ({'Postgres' if USE_POSTGRES else 'SQLite'}).")
    print("Datos de ejemplo cargados: 2 clientes, 5 productos, 3 compras, 5 items.")


if __name__ == "__main__":
    main()