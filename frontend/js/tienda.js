const $ = (sel) => document.querySelector(sel);
let solicitudActual = null;

async function buscarCodigo() {
  const codigo = $("#codigo").value.trim();
  const contMensaje = $("#mensaje_busqueda");
  contMensaje.innerHTML = "";
  $("#seccion_detalle").style.display = "none";
  $("#seccion_revision").style.display = "none";

  if (!codigo) return;

  const resp = await fetch(`/api/devoluciones/codigo/${encodeURIComponent(codigo)}`);
  const datos = await resp.json();

  if (!resp.ok) {
    contMensaje.innerHTML = `<div class="mensaje error">${datos.mensaje}</div>`;
    return;
  }

  solicitudActual = datos;
  $("#seccion_detalle").style.display = "block";
  $("#detalle_solicitud").innerHTML = `
    <div class="solicitud-linea">
      <span><strong>${datos.producto}</strong> (${datos.categoria})</span>
    </div>
    <div class="solicitud-linea"><span>Cliente</span><span>${datos.cliente}</span></div>
    <div class="solicitud-linea"><span>Motivo del cliente</span><span>${datos.motivo_cliente}</span></div>
    <div class="solicitud-linea"><span>Estado actual</span><span class="estado-tag ${datos.estado}">${datos.estado}</span></div>
  `;

  if (datos.estado === "aprobada_automatica") {
    $("#seccion_revision").style.display = "block";
  } else {
    contMensaje.innerHTML = `<div class="mensaje info">Esta solicitud ya fue procesada (estado: ${datos.estado}) y no admite una nueva revisión.</div>`;
  }
}

async function registrarRevision() {
  const contMensaje = $("#mensaje_revision");
  contMensaje.innerHTML = "";

  const empleado = $("#empleado").value;
  const condicion_producto = $("#condicion_producto").value;
  const comentario = $("#comentario").value;

  const resp = await fetch(`/api/devoluciones/codigo/${encodeURIComponent(solicitudActual.codigo_devolucion)}/revision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ empleado, condicion_producto, comentario }),
  });
  const datos = await resp.json();

  if (resp.ok) {
    const mensaje = datos.estado === "completada"
      ? "Devolución completada con éxito."
      : `Devolución rechazada en tienda: ${datos.motivo_rechazo}`;
    const clase = datos.estado === "completada" ? "exito" : "error";
    contMensaje.innerHTML = `<div class="mensaje ${clase}">${mensaje}</div>`;
    $("#btn_registrar_revision").disabled = true;

    solicitudActual.estado = datos.estado;
    const tagEstado = document.querySelector("#detalle_solicitud .estado-tag");
    if (tagEstado) {
      tagEstado.textContent = datos.estado;
      tagEstado.className = `estado-tag ${datos.estado}`;
    }
  } else {
    contMensaje.innerHTML = `<div class="mensaje error">${datos.mensaje}</div>`;
  }
}

$("#btn_buscar_codigo").addEventListener("click", buscarCodigo);
$("#btn_registrar_revision").addEventListener("click", registrarRevision);