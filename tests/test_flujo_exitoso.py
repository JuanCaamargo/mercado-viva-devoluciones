"""
Prueba 1 — Flujo exitoso.

Un cliente devuelve un producto elegible (dentro de la ventana de
devolución y de una categoría retornable). El empleado de tienda
verifica el producto en buen estado y la devolución queda completada.
"""


def test_flujo_completo_de_devolucion_exitosa(client):
    # 1. El cliente consulta sus compras y ve el producto como elegible
    resp = client.get("/api/clientes/1/compras")
    assert resp.status_code == 200
    compras = resp.get_json()["compras"]
    compra_reciente = next(c for c in compras if c["dias_transcurridos"] <= 30)
    item_licuadora = compra_reciente["items"][0]
    assert item_licuadora["producto"] == "Licuadora Vivax 600W"
    assert item_licuadora["elegible_para_devolucion"] is True

    # 2. El cliente solicita la devolución
    resp = client.post(
        "/api/devoluciones",
        json={"item_compra_id": item_licuadora["item_compra_id"], "motivo_cliente": "Ya no lo necesito"},
    )
    assert resp.status_code == 201
    datos = resp.get_json()
    assert datos["estado"] == "aprobada_automatica"
    codigo = datos["codigo_devolucion"]
    assert codigo.startswith("DEV-")

    # 3. El empleado de tienda consulta el código
    resp = client.get(f"/api/devoluciones/codigo/{codigo}")
    assert resp.status_code == 200
    solicitud = resp.get_json()
    assert solicitud["estado"] == "aprobada_automatica"
    assert solicitud["producto"] == "Licuadora Vivax 600W"

    # 4. El empleado verifica el producto en buen estado y completa la devolución
    resp = client.post(
        f"/api/devoluciones/codigo/{codigo}/revision",
        json={"empleado": "Carlos Pérez", "condicion_producto": "buen_estado"},
    )
    assert resp.status_code == 200
    resultado = resp.get_json()
    assert resultado["estado"] == "completada"

    # 5. El cliente puede ver el nuevo estado en su historial
    resp = client.get("/api/clientes/1/devoluciones")
    solicitudes = resp.get_json()["solicitudes"]
    encontrada = next(s for s in solicitudes if s["codigo_devolucion"] == codigo)
    assert encontrada["estado"] == "completada"