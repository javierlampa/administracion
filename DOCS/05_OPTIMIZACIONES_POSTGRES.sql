-- 05 — OPTIMIZACIONES DE BASE DE DATOS (POSTGRESQL)
-- Aplicar estos comandos en el Editor SQL de Supabase para mejorar el rendimiento.

---
-- 1. BUSCADORES TRÍGRAM (Búsqueda Parcial Ultrarrápida)
-- Permite que búsquedas como "Muni" encuentren "Municipalidad de San Juan" de forma instantánea 
-- incluso en tablas de millones de registros.
---

-- Habilitar extensión necesaria
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Índice para el Buscador de Clientes (Tabla Clientes)
CREATE INDEX IF NOT EXISTS idx_clientes_nombre_trgm 
ON public.clientes 
USING gin (nombre_comercial gin_trgm_ops);

-- Índice para el Buscador Desnormalizado (Tabla de Órdenes)
CREATE INDEX IF NOT EXISTS idx_op_cliente_nombre_trgm 
ON public.ordenes_publicidad 
USING gin (cliente_nombre gin_trgm_ops);

-- Índice para Programas (Tabla TV)
CREATE INDEX IF NOT EXISTS idx_tv_programa_trgm 
ON public.tv 
USING gin (programa_nombre gin_trgm_ops);


---
-- 2. ÍNDICES DE COMPOSICIÓN (Filtros de Reportes)
---

-- Indexar OP_REF en tabla TV para cruces (Joins) más rápidos
CREATE INDEX IF NOT EXISTS idx_tv_op_ref ON public.tv(op_ref);

-- Indexar Vendedor + Fecha para el reporte de Pagos/Auditoría
CREATE INDEX IF NOT EXISTS idx_pagos_vendedor_fecha ON public.pagos(vendedor, fecha_pago);

---
-- RECOMENDACIÓN: Ejecutar "ANALYZE;" después de crear los índices para que Postgres actualice sus planes.
ANALYZE public.clientes;
ANALYZE public.ordenes_publicidad;
ANALYZE public.tv;
ANALYZE public.pagos;
