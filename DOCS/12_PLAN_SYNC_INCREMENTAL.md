# Plan: Sincronizador Incremental Robusto para Pagos

## El Problema Resuelto (Abril 2026)
Durante la sincronización de la tabla `Pagos` desde SharePoint hacia Supabase, enfrentamos una grave discrepancia de datos donde los totales cobrados en el portal Next.js diferían por casi 35 millones frente a los reportes de facturación de PowerBI.

**Causas Raíz Identificadas:**
1. **Conflicto de Nomenclatura ID vs Texto:** En SharePoint, el campo `OP` para la tabla Pagos es un campo tipo `Lookup`. La Graph API, por lo tanto, devuelve el `ID interno de SharePoint` (ej: 7041, 1330) de la orden en lugar de su texto real (ej: "102/0").
2. **Colisiones Aleatorias:** Algunas Órdenes de Publicidad (OP) en el sistema literalmente se llamaban con texto numérico como "1330" o "7041". Al mapear, la función de sincronización veía que SharePoint enviaba el ID "1330", y en vez de buscar a qué OP real apuntaba ese ID de sistema, lo vinculaba erróneamente con la OP que se llamaba explícitamente "1330" (un caso completamente distinto). Esto asiló o sumergió millones de pesos en OPs equivocadas.

**Solución Aplicada:**
Se desarrolló e implementó el atributo `is_lookup` en la función compartida `smart_find_op_numero` y `smart_find_op_id` (en `sharepoint_sync.py`). 
Cuando el script procesa la lista de `Pagos`, fuerza la prioridad por `ID`. Literalmente dice: *"Sé que esto es un campo Lookup, por lo tanto, no intentes hacer coincidir strings. Busca primero el ID de SharePoint rigurosamente"*. 
Esto validó correctamente los 6776 pagos y el nivel de paridad con PowerBI fue restaurado al 100% (105M exactos cobrados en el tramo Q1 2026).

---

## Próximos Pasos: Sincronizador Incremental Activo
Actualmente el reparo lo realizamos limpiando toda la tabla e inyectando de 0 a través de `limpiar_y_recargar_pagos.py`. Sin embargo, esto es destructivo y no escalable. A continuación el plan para la **sincronización incremental futura**:

### 1. Actualización de `sharepoint_sync.py`
El archivo base `sharepoint_sync.py` ya posee la lógica para descargar **solo lo modificado** en las últimas horas, no obstante, debemos auditar y asegurar lo siguiente:

- **Mapeo Activo:** El diccionario en memoria (`get_global_ops_map()`) debe invocarse siempre antes de procesar el delta de pagos. Ya devuelve los 3 mapas necesarios (`map_str`, `map_id`, `map_id_to_op`) requeridos por el fijado `smart_find_op_numero`.
- **Detección Upsert de IDs:** Al importar pagos nuevos o modificados de SharePoint, el backend usa una función `lambda f: { ... }` para inyectar a PostgreSQL. Debido a que el OPLookupId ahora se formatea y se inserta obligatoriamente bajo `op_numero`, se debe asegurar que la estructura del *upsert* compare el ID original de Supabase (pagos.id) para que no duplique registros tras las pasadas incrementales. 
- **Flags de Operación:** En el mapeo de listas dentro de `run_incremental_sync()`, verificar categóricamente que en la tupla que procesa `"Pagos"` se mantenga enviado explicitamente `is_lookup=True` al llamar a la conversión.

### 2. Flujo Propuesto a Implementar
1. **Delta Pull:** Cronograma consulta la API de M365 con filtro cronometrado de las últimas 3-6 horas `&$filter=Modified ge '...'`.
2. **Construcción Contexto:** Supabase pre-carga diccionarios de UN, TV y OPs en milisegundos.
3. **Parseo Estricto:** Iterar pagos, y traducir estáticamente los Lookup IDs al `op_numero` verdadero.
4. **Merge DB:** Ejecutar `upsert` basado en un Key ID artificial (Ejemplo: `recibo_numero` combinado con el identificador en SP). Esto garantizará que una misma partida paga alterada en Sharepoint actualice el mismo pago en la BD sin borrar ni duplicar.

Este documento debe ser usado como pre-requisito cuando vayamos a migrar completamente la ingesta hacia ejecuciones CRON o *Edge Functions* de Supabase.
