"""
Prueba 2 — Caso excepcional.

El cliente intenta devolver una compra que ya superó la ventana de
devolución de 30 días. El sistema debe rechazar la solicitud
automáticamente, explicar el motivo y no debe quedar una devolución
aprobada para gestionar en tienda.
"""


def test_rechaza_devolucion_fuera_de_la_ventana_permitida(client):
    resp = client.get("/api/clientes/1/compras")
    compras = resp.get_json()["compras"]
    compra_vieja = next(c for c in compras if c["dias_transcurridos"] > 30)
    item_fuera_de_ventana = compra_vieja["items"][0] 

    assert item_fuera_de_ventana["elegible_para_devolucion"] is False
    assert "días" in item_fuera_de_ventana["motivo_no_elegible"]

    resp = client.post(
        "/api/devoluciones",
        json={
            "item_compra_id": item_fuera_de_ventana["item_compra_id"],
            "motivo_cliente": "Cambié de opinión",
        },
    )

    assert resp.status_code == 422
    datos = resp.get_json()
    assert datos["error"] is True
    assert datos["codigo_error"] == "DEVOLUCION_NO_ELEGIBLE"
    assert "30 días" in datos["mensaje"]

    resp = client.get("/api/clientes/1/devoluciones")
    solicitudes = resp.get_json()["solicitudes"]
    rechazada = next(
        s for s in solicitudes if s["producto"] == "Set de sartenes antiadherentes"
    )
    assert rechazada["estado"] == "rechazada_automatica"


def test_producto_no_retornable_por_categoria_se_rechaza(client):
    resp = client.get("/api/clientes/2/compras")
    compras = resp.get_json()["compras"]
    item_leche = compras[0]["items"][0]
    assert item_leche["producto"] == "Leche entera x 1L"
    assert item_leche["elegible_para_devolucion"] is False

    resp = client.post(
        "/api/devoluciones",
        json={"item_compra_id": item_leche["item_compra_id"], "motivo_cliente": "Empaque abierto"},
    )
    assert resp.status_code == 422
    assert "no admite devoluciones" in resp.get_json()["mensaje"]