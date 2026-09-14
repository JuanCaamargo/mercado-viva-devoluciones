const $ = (sel) => document.querySelector(sel);

function formatoMoneda(valor) {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(valor);
}

function etiquetaEstado(estado) {
  const textos = {
    aprobada_automatica: "Aprobada — pendiente en tienda",
    completada: "Completada",
    rechazada_automatica: "Rechazada",
    rechazada_tienda: "Rechazada en tienda",
  };
  return `<span class="estado-tag ${estado}">${textos[estado] || estado}</span>`;
}

async function cargarCompras(clienteId, opciones = {}) {
  const contMensaje = $("#mensaje_compras");
  contMensaje.innerHTML = "";
  if (!opciones.conservarMensajeAccion) {
    $("#mensaje_accion").innerHTML = "";
  }

  const resp = await fetch(`/api/clientes/${clienteId}/compras`);
  const datos = await resp.json();

  if (!resp.ok) {
    contMensaje.innerHTML = `<div class="mensaje error">${datos.mensaje}</div>`;
    $("#seccion_compras").style.display = "none";
    return;
  }

  $("#seccion_compras").style.display = "block";
  const cont = $("#lista_compras");

  if (datos.compras.length === 0) {
    cont.innerHTML = `<p class="muted">Este cliente no tiene compras registradas.</p>`;
    return;
  }

  cont.innerHTML = datos.compras
    .map((compra) => {
      const itemsHtml = compra.items
        .map((item) => {
          const badge = item.elegible_para_devolucion
            ? `<span class="badge elegible">Elegible</span>`
            : `<span class="badge no-elegible" title="${item.motivo_no_elegible}">No elegible</span>`;

          const accion = item.elegible_para_devolucion
            ? `
              <div class="fila" style="margin-top:0.4rem;">
                <input type="text" placeholder="Motivo de la devolución" id="motivo_${item.item_compra_id}">
                <button data-item="${item.item_compra_id}" class="btn-solicitar">Solicitar</button>
              </div>
            `
            : `<div class="muted">${item.motivo_no_elegible}</div>`;

          return `
            <div class="item-linea" style="flex-direction:column; align-items:stretch;">
              <div class="item-info">
                <strong>${item.producto}</strong> (${item.cantidad} u.) — ${formatoMoneda(item.precio_unitario)}
                ${badge}
              </div>
              ${accion}
            </div>
          `;
        })
        .join("");

      return `
        <div class="compra">
          <div class="muted">Compra #${compra.compra_id} · canal ${compra.canal} · hace ${compra.dias_transcurridos} días</div>
          ${itemsHtml}
        </div>
      `;
    })
    .join("");

  document.querySelectorAll(".btn-solicitar").forEach((btn) => {
    btn.addEventListener("click", () => solicitarDevolucion(btn.dataset.item, clienteId));
  });
}

async function solicitarDevolucion(itemCompraId, clienteId) {
  const motivoInput = $(`#motivo_${itemCompraId}`);
  const motivo = motivoInput.value;
  const contAccion = $("#mensaje_accion");

  const resp = await fetch("/api/devoluciones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_compra_id: Number(itemCompraId), motivo_cliente: motivo }),
  });
  const datos = await resp.json();

  if (resp.ok) {
    contAccion.innerHTML = `
      <div class="mensaje exito">
        Solicitud creada. Tu código de devolución es <span class="codigo">${datos.codigo_devolucion}</span>.
        Preséntalo en tienda junto con el producto.
      </div>`;
  } else {
    contAccion.innerHTML = `<div class="mensaje error">${datos.mensaje}</div>`;
  }

  await cargarCompras(clienteId, { conservarMensajeAccion: true });
  await cargarSolicitudes(clienteId);
}

async function cargarSolicitudes(clienteId) {
  const resp = await fetch(`/api/clientes/${clienteId}/devoluciones`);
  const datos = await resp.json();
  if (!resp.ok) return;

  $("#seccion_solicitudes").style.display = "block";
  const cont = $("#lista_solicitudes");

  if (datos.solicitudes.length === 0) {
    cont.innerHTML = `<p class="muted">Aún no tienes solicitudes de devolución.</p>`;
    return;
  }

  cont.innerHTML = datos.solicitudes
    .map(
      (s) => `
      <div class="solicitud-linea">
        <span><span class="codigo">${s.codigo_devolucion}</span> — ${s.producto}</span>
        ${etiquetaEstado(s.estado)}
      </div>
      ${s.motivo_rechazo ? `<div class="muted" style="margin-bottom:0.4rem;">${s.motivo_rechazo}</div>` : ""}
    `
    )
    .join("");
}

$("#btn_buscar_compras").addEventListener("click", async () => {
  const clienteId = $("#cliente_id").value;
  if (!clienteId) return;
  await cargarCompras(clienteId);
  await cargarSolicitudes(clienteId);
});