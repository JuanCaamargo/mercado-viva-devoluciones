

DROP TABLE IF EXISTS revisiones_tienda CASCADE;
DROP TABLE IF EXISTS solicitudes_devolucion CASCADE;
DROP TABLE IF EXISTS items_compra CASCADE;
DROP TABLE IF EXISTS compras CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;

CREATE TABLE clientes (
    id              SERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE
);

CREATE TABLE productos (
    id              SERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,
    categoria       TEXT NOT NULL,
    precio_unitario NUMERIC(12, 2) NOT NULL,
    es_retornable   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE compras (
    id              SERIAL PRIMARY KEY,
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id),
    canal           TEXT NOT NULL DEFAULT 'app',
    fecha_compra    TIMESTAMP NOT NULL
);

CREATE TABLE items_compra (
    id              SERIAL PRIMARY KEY,
    compra_id       INTEGER NOT NULL REFERENCES compras(id),
    producto_id     INTEGER NOT NULL REFERENCES productos(id),
    cantidad        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE solicitudes_devolucion (
    id                    SERIAL PRIMARY KEY,
    item_compra_id        INTEGER NOT NULL REFERENCES items_compra(id),
    codigo_devolucion     TEXT NOT NULL UNIQUE,
    motivo_cliente        TEXT NOT NULL,
    estado                TEXT NOT NULL,
    motivo_rechazo        TEXT,
    fecha_solicitud       TIMESTAMP NOT NULL,
    fecha_resolucion      TIMESTAMP
);

CREATE TABLE revisiones_tienda (
    id                    SERIAL PRIMARY KEY,
    solicitud_id          INTEGER NOT NULL REFERENCES solicitudes_devolucion(id),
    empleado              TEXT NOT NULL,
    condicion_producto    TEXT NOT NULL,
    comentario            TEXT,
    fecha_revision        TIMESTAMP NOT NULL
);

CREATE INDEX idx_compras_cliente ON compras(cliente_id);
CREATE INDEX idx_items_compra ON items_compra(compra_id);
CREATE INDEX idx_solicitudes_item ON solicitudes_devolucion(item_compra_id);
CREATE INDEX idx_solicitudes_codigo ON solicitudes_devolucion(codigo_devolucion);