-- Esquema de base de datos: Módulo de Devoluciones Digitales — Mercado VIVA
-- Motor: SQLite 

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS revisiones_tienda;
DROP TABLE IF EXISTS solicitudes_devolucion;
DROP TABLE IF EXISTS items_compra;
DROP TABLE IF EXISTS compras;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS clientes;

CREATE TABLE clientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE
);

-- es_retornable: regla de negocio a nivel de categoría (ej. perecederos no se devuelven)
CREATE TABLE productos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    categoria       TEXT NOT NULL,
    precio_unitario REAL NOT NULL,
    es_retornable   INTEGER NOT NULL DEFAULT 1  -- 1 = sí, 0 = no
);

CREATE TABLE compras (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL,
    canal           TEXT NOT NULL DEFAULT 'app',   -- app | web
    fecha_compra    TEXT NOT NULL,                 -- ISO 8601
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE items_compra (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id       INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (compra_id) REFERENCES compras(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- estado: pendiente_revision | aprobada_automatica | rechazada_automatica
--         | completada | rechazada_tienda
CREATE TABLE solicitudes_devolucion (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    item_compra_id        INTEGER NOT NULL,
    codigo_devolucion     TEXT NOT NULL UNIQUE,
    motivo_cliente        TEXT NOT NULL,
    estado                TEXT NOT NULL,
    motivo_rechazo        TEXT,
    fecha_solicitud       TEXT NOT NULL,
    fecha_resolucion      TEXT,
    FOREIGN KEY (item_compra_id) REFERENCES items_compra(id)
);

-- Registro de la verificación física hecha por el empleado en tienda
CREATE TABLE revisiones_tienda (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id          INTEGER NOT NULL,
    empleado              TEXT NOT NULL,
    condicion_producto    TEXT NOT NULL,  -- buen_estado | dañado | incompleto
    comentario            TEXT,
    fecha_revision        TEXT NOT NULL,
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes_devolucion(id)
);