# Mercado VIVA · Módulo de Devoluciones Digitales

MVP funcional para el proceso **"Devolución de una compra digital"**, desarrollado
como parte del taller de Fundamentos de Diseño e Implementación de Software.

---

## 1. Definición

### Problema seleccionado

Mercado VIVA es una cadena de supermercados con tiendas físicas y canales
digitales. Hoy, cuando un cliente compra por la app o la web y quiere
devolver el producto en una tienda física, el proceso es manual: el
empleado no tiene forma de verificar rápidamente si la compra es real, si
cumple las condiciones para devolverse, ni de dejar un registro consistente
del resultado. Esto genera reprocesos, tiempos de atención largos y
decisiones distintas según quién atienda al cliente.

Este MVP ataca un recorte pequeño y concreto de ese problema: **darle al
cliente una forma de solicitar y pre-validar su devolución antes de ir a la
tienda, y darle al empleado una forma de verificar esa solicitud con un
código, en vez de reconstruir todo el caso desde cero.**

### Usuarios involucrados

| Usuario | Rol en el proceso |
|---|---|
| **Cliente** | Compró un producto por app/web y quiere devolverlo en tienda física. |
| **Empleado de tienda** | Recibe al cliente, verifica el producto físicamente y decide si la devolución se completa. |

### Objetivo y alcance del MVP

**Objetivo:** que un cliente pueda solicitar la devolución de una compra
digital y saber de inmediato si es elegible, y que un empleado de tienda
pueda verificar esa solicitud con un código y resolverla, sin pasos
manuales adicionales.

**Alcance:**
- Consultar las compras de un cliente y marcar qué productos son elegibles para devolución.
- Validar automáticamente dos reglas de negocio: ventana de tiempo desde la compra, y categoría del producto.
- Generar un código de devolución único cuando la solicitud es aprobada.
- Permitir que un empleado busque ese código, registre el estado físico del producto y complete o rechace la devolución.
- Dejar trazabilidad de cada intento, incluso los rechazados.

---

## 2. Historias de usuario

### HU1 — Ver qué compras puedo devolver

**Como** cliente, **quiero** ver mis compras marcadas como elegibles o no
para devolución, **para** saber de una vez si vale la pena ir a la tienda.

- **Dado** que tengo una compra hecha hace menos de 30 días con un producto de categoría retornable, **cuando** consulto mis compras, **entonces** el producto aparece marcado como "Elegible".
- **Dado** que tengo una compra hecha hace más de 30 días, **cuando** la consulto, **entonces** aparece como "No elegible" con el motivo explicado.

### HU2 — Solicitar una devolución

**Como** cliente, **quiero** solicitar la devolución de un producto elegible
indicando un motivo, **para** obtener un código que pueda llevar a la tienda.

- **Dado** un producto elegible, **cuando** envío la solicitud con un motivo no vacío, **entonces** el sistema me entrega un código de devolución único y la solicitud queda "aprobada automáticamente".
- **Dado** que no escribo ningún motivo, **cuando** intento enviar la solicitud, **entonces** el sistema la rechaza y me pide completar el campo.

### HU3 — Que el sistema rechace automáticamente lo que no cumple

**Como** cliente, **quiero** que el sistema me explique por qué no puedo
devolver algo, **para** no perder tiempo yendo a la tienda sin motivo.

- **Dado** un producto de una categoría no retornable (por ejemplo, perecederos), **cuando** intento solicitar su devolución, **entonces** el sistema la rechaza automáticamente y me muestra el motivo exacto.
- **Dado** un producto elegible que ya tiene una solicitud en curso, **cuando** intento solicitarlo de nuevo, **entonces** el sistema me avisa que ya existe una solicitud para ese producto.

### HU4 — Verificar una solicitud en tienda

**Como** empleado de tienda, **quiero** buscar una solicitud por su código,
**para** confirmar que es una devolución autorizada y ver los datos del
cliente y el producto antes de revisarlo físicamente.

- **Dado** un código válido y con estado "aprobada automáticamente", **cuando** lo busco, **entonces** veo el cliente, el producto y el motivo, y se habilita el formulario de revisión.
- **Dado** un código que no existe, **cuando** lo busco, **entonces** el sistema muestra un error claro y no rompe la página.

### HU5 — Completar o rechazar la devolución en tienda

**Como** empleado de tienda, **quiero** registrar el estado físico del
producto y con eso decidir si la devolución se completa, **para** dejar un
resultado único y consistente sin importar quién atienda.

- **Dado** una solicitud aprobada, **cuando** registro el producto como "buen estado", **entonces** la devolución pasa a "completada" y el cliente puede verlo en su historial.
- **Dado** una solicitud aprobada, **cuando** registro el producto como "dañado" o "incompleto", **entonces** la devolución pasa a "rechazada en tienda" con el motivo registrado.
- **Dado** una solicitud que ya fue procesada antes, **cuando** intento registrar otra revisión sobre el mismo código, **entonces** el sistema lo impide y explica que ya fue resuelta.

---

## 3. Diseño preliminar

### Pasos principales del proceso

1. El cliente ingresa su identificador (simulación de sesión para el MVP).
2. El cliente consulta sus compras; el sistema calcula, por cada producto, si es elegible para devolución.
3. El cliente elige un producto elegible y escribe un motivo.
4. El sistema aplica las reglas de negocio (ventana de tiempo, categoría, solicitud previa) y decide si aprueba o rechaza automáticamente.
5. Si aprueba, genera un código de devolución único y lo entrega al cliente.
6. El cliente lleva el producto físico y el código a una tienda.
7. El empleado busca el código y ve el detalle de la solicitud.
8. El empleado revisa el producto físicamente y registra su estado (buen estado / dañado / incompleto).
9. El sistema decide, con base en esa revisión, si la devolución queda completada o rechazada en tienda.
10. El cliente puede consultar en cualquier momento el estado final de su solicitud.

### Información que ingresa, se consulta o se modifica

**Ingresa:**
- Del cliente: identificador, producto elegido, motivo de la devolución.
- Del empleado: código a buscar, nombre del empleado, estado físico del producto, comentario opcional.

**Se consulta:**
- Compras e items del cliente, con su elegibilidad calculada al vuelo.
- Detalle de una solicitud a partir de su código.
- Historial de solicitudes de un cliente.

**Se modifica:**
- Se crea un registro nuevo en `solicitudes_devolucion` en cada intento (aprobado o rechazado, para trazabilidad).
- Se actualiza el estado de la solicitud cuando el empleado registra su revisión.
- Se inserta un registro en `revisiones_tienda` con el resultado de la inspección física.

### Flujo de información entre frontend, backend y base de datos

El frontend (HTML/CSS/JS) nunca habla directo con la
base de datos: todo pasa por una API HTTP expuesta por el backend Flask.

```
Frontend (fetch)  →  API Flask (/api/...)  →  Capa de reglas de negocio  →  SQLite
      ↑                                                                        │
      └────────────────────── respuesta JSON ─────────────────────────────────┘
```

- El **frontend** solo sabe hacer `fetch()` a rutas como `/api/clientes/<id>/compras` o `/api/devoluciones`, y pintar lo que reciba.
- El **backend** recibe la petición, valida el formato de los datos, aplica las reglas de negocio (en una capa de "servicio" separada de las rutas) y traduce el resultado a un código HTTP y un JSON.
- La **base de datos** SQLite solo almacena datos; no contiene lógica de negocio para que las reglas queden legibles en un solo lugar del código Python.

### Validaciones y posibles errores

| Situación | Qué hace el sistema |
|---|---|
| Motivo de devolución vacío | Rechaza con error 400 antes de tocar la base de datos. |
| Producto de categoría no retornable | Rechaza automáticamente (422) con el motivo explicado. |
| Compra fuera de la ventana de 30 días | Rechaza automáticamente (422), indicando cuántos días han pasado. |
| Producto con una solicitud previa activa | Rechaza con conflicto (409), evitando doble devolución. |
| Código de devolución inexistente | Devuelve error 404 con mensaje claro, tanto al buscarlo como al revisarlo. |
| Solicitud ya resuelta y se intenta revisar de nuevo | Rechaza con conflicto (409): no se puede reprocesar. |
| Falla al conectar con el servidor | El frontend muestra un mensaje de error genérico sin romper la página (manejo de `fetch` con verificación de `resp.ok`). |

---