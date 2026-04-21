# Vinculaciones SharePoint -> Supabase

Este documento detalla la arquitectura de sincronización para asegurar la integridad de los datos financieros.

## 🔑 Clave de Negocio (El Corazón del Sistema)
La unión entre SharePoint y Supabase NO se hace mediante IDs numéricos de SharePoint (que pueden cambiar en cada lista), sino mediante el **Número de OP**.

### Reglas de Limpieza de OP (`clean_op`)
Para evitar errores de vinculación (ej. `4035` vs `4035.0`), el sistema aplica:
1. Eliminación de decimales `.0` al final.
2. Limpieza de espacios en blanco y caracteres invisibles.
3. Conversión a string para tratamiento uniforme.

## 🔄 Lógica de Sincronización

### 1. Tabla Maestra (`ordenes_publicidad`)
- **Modo:** Upsert (Update or Insert) basado en la columna `op`.
- **Limpieza de Huérfanos:** El script detecta órdenes que existen en Supabase pero ya no en SharePoint y las elimina automáticamente.

### 2. Tablas Hijas (`unidades_negocio`, `tv`, `pagos`)
- **Modo:** **Espejo Total (Mirror Sync)**.
- **Acción:** En cada corrida, el sistema limpia la tabla completa en Supabase (`DELETE *`) e inyecta la versión más reciente de SharePoint.
- **Razón:** Esto garantiza que si una unidad de negocio se borra en SharePoint, desaparezca instantáneamente del Portal, manteniendo paridad absoluta.

## 📊 Mapeo de Columnas Técnicas
Debido a que la API Graph de Microsoft usa nombres internos, se debe respetar el siguiente mapeo para la lista **"Unidad de Negocio"**:
- **Unidad:** `Unidaddenegocio0`
- **Importe Total:** `ImporteTotal`
- **IVA:** `IVA0` (Conversión de `,` a `.` obligatoria)
- **Importe sin IVA:** `ImportesinIVA`

## 🚀 Paginación y Escalamiento
- Consultas a Supabase: Bloques de 1.000 con `range(i, i+999)`.
- Capacidad actual: Hasta 50.000 registros.
