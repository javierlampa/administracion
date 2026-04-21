**Última actualización:** 15 de Abril 2026 · Sistema: Telesol

---

## 9. SESIÓN 15/04/2026 — SYNC INCREMENTAL ROBUSTO + REPORTES DUALES

### Objetivo
Estabilizar `sharepoint_sync.py` para que corra 24/7 sin intervención manual, saltee errores individuales (duplicados, huérfanos) sin detener el proceso, y genere reportes claros de qué se actualizó y qué falló.

### Cambios en `sharepoint_sync.py`

#### Sincronización Incremental
- Ventana de 12 horas hacia atrás en cada ciclo (evita reprocesar todo)
- Bucle infinito `while True` con `time.sleep(3600)` — corre cada 1 hora
- Token Microsoft renovado al inicio de cada ciclo completo

#### Manejo de Duplicados y Errores
- **OPs duplicadas:** Antes de subir, verifica si el número de OP ya existe en DB → la saltea sin error
- **Upsert granular:** Cada registro (OP, TV, UN, Pago) se inserta individualmente con `try/except`
- **Criterio de unicidad:** El número de OP real (`op_numero`), no el ID interno

#### Sistema de Reportes Duales
- `DOCS/sincronizacion_exitosa.txt` → OPs actualizadas correctamente, agrupadas por tabla
- `DOCS/sincronizacion_errores.txt` → Errores con Lista | OP | SP_ID | Motivo
- `DOCS/reporte_huerfanos.txt` → Eliminado (reemplazado por los dos archivos de arriba)

### Reorganización del Proyecto
- Scripts de prueba/diagnóstico → `archive/scripts/`
- Archivos de datos → `archive/data/`
- Migraciones SQL → `database/sql/`
- `apply_sql.py` y `apply_sql_monitoring.py` → rutas actualizadas
- Git inicializado con `.gitignore` correcto (`.env` excluido)

---


## 8. SESIÓN 13/04/2026 — BOT WHATSAPP V3 (NAVEGACIÓN POR ESTADOS)

### Objetivo
Reemplazar el bot basado en IA (Gemini) por una **máquina de estados** determinista que guía al usuario por menús numerados, eliminando respuestas ambiguas y mezcla de datos.

### Cambios en `whatsapp_bot.py`

#### Estados definidos
```python
STATE_ROOT          = "ROOT"
STATE_WAITING_NAME  = "WAITING_NAME"
STATE_WAITING_CONFIRM = "WAITING_CONFIRM"
STATE_MENU_ACTIVE   = "MENU_ACTIVE"
```

#### Nuevas funciones implementadas
| Función | Descripción |
|---|---|
| `handle_root_state()` | Muestra menú inicial: Cliente o Vendedor |
| `handle_waiting_name_state()` | Busca en DB filtrando por tipo de entidad |
| `handle_waiting_confirm_state()` | Confirma si la entidad encontrada es la correcta |
| `handle_menu_active_state()` | Despacha la acción según el menú de rol (Cliente/Vendedor) |
| `consultar_pauta_hoy(entidad, tipo)` | Pauta activa hoy, filtrando por cliente o vendedor |
| `consultar_comisiones_vendedor(vendedor)` | Resumen de comisiones de un vendedor específico |

#### Refactorizado
| Función | Cambio |
|---|---|
| `buscar_datos_sistema(texto, tipo)` | Ahora acepta parámetro `tipo` ('CLIENTE'/'VENDEDOR') para filtrar resultados |
| `generar_reporte_pdf()` | Actualizado a sintaxis moderna de fpdf2 (sin deprecation warnings) |
| `send_whatsapp_media()` | Corregido: usa campo `media` y base64 puro sin prefijo `data:` |
| `webhook()` | Refactorizado como dispatcher puro: lee estado → llama al handler correcto |

#### Menús activos
```
ROOT:       [1] 👤 Por Cliente  /  [2] 💼 Por Vendedor
CLIENTE:    [1] Saldo  [2] Pauta Hoy  [3] Ver OPs  [4] PDF  [0] Inicio
VENDEDOR:   [1] Comisiones  [2] Saldos Clientes  [3] Resumen Ventas  [4] Excel  [0] Inicio
```

### Docs actualizadas
- `DOCS/10_PROJECT_STATE.md` — Estado general del sistema
- `DOCS/implementation_plan_v3.md` — Plan técnico V3 marcado como implementado
- `DOCS/06_BUGS_Y_OPTIMIZACIONES.md` — Bugs de esta sesión documentados
- `DOCS/11_CONTEXTO_BOT_WHATSAPP.md` — **NUEVO** — Contexto completo del bot

---

## 1. ESQUEMA REAL DE BASE DE DATOS (verificado con information_schema)

### `ordenes_publicidad` — Tabla principal
| Columna | Tipo | Descripción |
|---|---|---|
| id | integer | PK |
| op | text | Número de Orden de Publicidad |
| empresa | text | Texto directo (ej: "ANDINA SA") |
| fecha_orden | date | Fecha de la orden |
| inicio_pauta | date | Inicio de la pauta publicitaria |
| fin_pauta | date | Fin de la pauta publicitaria |
| fecha_factura | date | Fecha de la factura |
| fecha_creacion | date | Fecha de creación en SharePoint |
| esta_facturado | boolean | SI/NO facturado |
| es_canje | boolean | SI/NO es canje |
| numero_factura | text | Número de factura |
| tipo_factura | text | Tipo de factura (A, B, etc.) |
| importe_total | numeric | Importe total con IVA |
| importe_sin_iva | numeric | Importe sin IVA |
| iva | numeric | Porcentaje de IVA |
| cliente_id | integer | FK → clientes.id |
| cliente_nombre | text | Nombre guardado directo (desnormalizado) |
| vendedor_id | integer | FK → vendedores.id |
| vendedor_nombre | text | Nombre guardado directo (desnormalizado) |
| clasificacion | text | Clasificación del cliente |
| venta_combo | boolean | Es venta combo |
| anio | integer | Año de la orden |
| medidas_digital | text | Medidas del espacio digital |
| modulos_papel | text | Módulos en papel |
| created | timestamp | Fecha de creación SP |
| modified | timestamp | Fecha de modificación SP |
| activo | boolean | Registro activo |

### `unidades_negocio` — Una fila por unidad de negocio de cada OP
| Columna | Tipo | Descripción |
|---|---|---|
| id | integer | PK |
| op_ref | text | Referencia OP (OP_UNN en SharePoint) |
| op_id | integer | FK → ordenes_publicidad.id |
| unidad_negocio | text | Nombre de la unidad (ej: "Radio 1020") |
| importe_total | numeric | Importe para esta unidad |
| importe_sin_iva | numeric | |
| iva | numeric | |

### `tv` — Una fila por pauta de TV/Radio
| Columna | Tipo | Descripción |
|---|---|---|
| id | integer | PK |
| op_ref | text | Referencia OP |
| op_id | integer | FK → ordenes_publicidad.id |
| programa_id | integer | FK → programas.id |
| programa_nombre | text | Nombre guardado directo (desnormalizado) |
| tipo | text | Tipo de pauta (SPOT, MENCIÓN, etc.) |
| importe_total | numeric | Importe de esta pauta |
| segundos | numeric | Duración en segundos |
| valor_segundo | numeric | Valor por segundo |

### `pagos` — Pagos recibidos por OP (Reconciliado con SharePoint)
| Columna | Tipo | Descripción |
|---|---|---|
| id | integer | PK |
| op_numero | text | Número de OP (ej: "6927") |
| op_id | integer | FK → ordenes_publicidad.id |
| fecha_pago | date | Fecha del pago |
| importe_pago | numeric | Monto bruto cobrado |
| total_sin_iva | numeric | Monto base calculado (Neto) |
| iva | numeric | % de IVA aplicado (0, 10.5, 21) |
| saldo | numeric | Saldo restante en la OP tras este pago (Libro Banco) |
| comision | numeric | % de comisión del vendedor (ej: 30) |
| importe_comision | numeric | Monto en $ de la comisión |
| recibo_numero | text | Nº de comprobante / recibo |
| medio_pago | text | EFECTIVO, TRANSFERENCIA, etc. |
| vendedor | text | Nombre del vendedor (desnormalizado) |
| cliente | text | Nombre del comercio (desnormalizado) |
| esta_liquidado | boolean | ¿Pago ya liquidado al vendedor? |
| fecha_liquidacion | date | Fecha de liquidación efectiva |

### `clientes`
| Columna | Descripción |
|---|---|
| id | PK |
| nombre_comercial | Nombre del comercio (usado en búsquedas) |
| razon_social | Razón social legal |
| cuit | CUIT del cliente |

### `vendedores`
| Columna | Descripción |
|---|---|
| id | PK |
| nombre | Nombre completo del vendedor |

---

## 2. INTEGRACIÓN CON SHAREPOINT (`sharepoint_sync.py`)

El script Python sincroniza listas de SharePoint con Supabase via Microsoft Graph API.

### Columnas Sincronizadas
| SP Column | DB Column | Notas |
|---|---|---|
| `ClasificacionClientes` | `clasificacion` | |
| `VentaCOMBO` | `venta_combo` | |
| `Empresa` | `empresa` | |
| `A_x00f1_o` | `anio` | La "ñ" viene codificada |
| `MedidasDigital` | `medidas_digital` | |
| `ModulosDiarioPapel` | `modulos_papel` | |
| `Dia` | `dia` | Habilitado en sync actual |
| `Mes` | `mes` | Habilitado en sync actual |

### Bucle Automático
El script ejecuta la sincronización en un loop con intervalo de 3600 segundos (1 hora).

---

## 3. ARQUITECTURA DE VISTAS SQL

**Patrón Definitivo:** Se delega toda la lógica de cruces y cálculo de saldos al motor PostgreSQL. El frontend consume datos ya procesados y enriquecidos.

| Vista SQL | Módulo Portal | Descripción |
|---|---|---|
| `v_todas_las_op_report` | `/reportes/todas_las_op` | Junta OP, Clientes, Vendedores y calcula `saldo_actual` |
| `v_pagos_resumen` | `/reportes/pagos` | Resumen de pagos, saldos y estado de cuenta por OP |
| `v_comisiones_report` | `/reportes/comisiones` | Analítico de pagos con datos de vendedor y cliente |
| `v_reporte_programas` | `/reportes/ventas-tv` | Detalle cruzado de pauta TV/Radio con datos de la OP |
| `v_dashboard_ranking_tv` | `/reportes/inicio_dash` | Ranking de facturación y KPIs para el dashboard |

---

## 4. ARQUITECTURA DE COMPONENTES (FRONTEND)

### Componente `ReportTable` — Fuente de Verdad Visual
**Ruta:** `/portal/src/components/DataTable/ReportTable.tsx`

Centraliza toda la lógica de visualización de tablas:
- **Virtual Scrolling:** Solo renderiza las filas visibles en pantalla → fluidez con miles de registros.
- **Columnas Dinámicas:** Sistema de columnas tipado con `Column<T>[]` configurable por módulo.
- **Estados de Carga:** Maneja `loading`, `hasSearched` y `emptyMessage` de forma consistente.
- **Soporte Master-Detail:** Filas expandibles para mostrar detalle adicional.

### Motor de Búsqueda "Smart Select"
Implementado en todos los módulos de reporte, reemplaza el `<datalist>` nativo:
- **Resaltado Dinámico (Highlight):** Las letras que coinciden con la búsqueda se muestran en **negrita + azul**.
- **Orden de Relevancia:** Los resultados que *comienzan* con el texto buscado aparecen primero.
- **Scroll Propio:** Máximo 50 resultados visibles con scroll interno, sin romper el layout.
- **Cierre Automático:** Se cierra al seleccionar o hacer click afuera (via `onBlur` + timeout).

### Biblioteca `formatters`
**Ruta:** `/portal/src/lib/formatters.ts`
- `formatCurrency(val)` → Formato ARS: `$1.234.567`
- `formatDate(val)` → Formato DD/MM/AAAA

---

## 5. ESTADO DE MIGRACIÓN DE MÓDULOS

| Módulo | Estado | Motor SQL | Tecnología UI |
|---|---|---|---|
| **Todas las OP** | ✅ Completado | `v_todas_las_op_report` | `ReportTable` + `SmartSelect` |
| **Programas TV / Radio** | ✅ Completado | `v_reporte_programas` | `ReportTable` + `SmartSelect` |
| **Comisiones** | ✅ Completado | `v_comisiones_report` | `ReportTable` + `SmartSelect` |
| **Pagos y Saldos** | ✅ Completado | `v_pagos_resumen` | Smart Export (Resumen vs Libro Banco) |
| **Dashboard** | ✅ Completado | `v_dashboard_ranking_tv` | KPIs + Rankings |
| **Carga de Pagos** | ✅ Completado | Ingesta Directa | Triple Search + Live Calculations |
| **Carga de Facturas / OP** | ✅ Completado | Ingesta Directa | Formularios React Dual-Theme |

### Política de UX: "Zero-Load Initial"
- La tabla **no carga datos al entrar** al módulo → página limpia y rápida.
- Los filtros de maestros (Vendedores, Clientes) **sí se cargan** al montar para poblar los dropdowns.
- Los datos se cargan **solo cuando el usuario presiona BUSCAR o Enter**.

### Lógica de Auditoría Automática
- **Alarma Roja (Inconsistencia):** Si `esta_facturado = SI` y `saldo_actual > 0` → OP facturada con saldo pendiente.
- **Indicador Visual:** Triángulo de advertencia `⚠` parpadeante en la fila y KPI de alerta en el header.
- **Saldos en Tiempo Real:** Sumarización automática en la cabecera tras cada búsqueda.
- **Motor de Exportación Híbrido:** Selector modal para elegir entre reporte resumido o detallado (Libro Banco / Detalle Técnico).
- **Ordenación Cronológica:** Exportaciones configuradas en orden ascendente (Primero el pago más viejo) para coherencia financiera.

---

## 6. LIBRERÍAS UTILIZADAS

| Librería | Uso |
|---|---|
| `@supabase/supabase-js` | Cliente de base de datos |
| `xlsx` | Export a Excel |
| `jspdf` + `jspdf-autotable` | Export a PDF |
| `lucide-react` | Iconos |
| `next.js 14` | Framework React |
| `tailwindcss` | Estilos |

---

## 7. SESIÓN 08/04/2026 — AUDITORÍA TÉCNICA Y OPTIMIZACIÓN

### Nuevas Funciones RPC agregadas a Supabase
| Función | Vista Base | Retorna |
|---|---|---|
| `get_report_totals(...)` | `v_todas_las_op_report` | `total_bruto`, `total_saldo`, `total_count` |
| `get_ventas_tv_totals(...)` | `v_reporte_programas` | `total_importe`, `total_segundos`, `total_count` |

### Nuevos Archivos del Portal
| Archivo | Descripción |
|---|---|
| `src/types/database.ts` | Interfaces TypeScript para todos los datos: `IOpRecord`, `IReportTotals`, etc. |

### Cambios de Arquitectura
| Componente | Cambio |
|---|---|
| `menuConfig.ts` | Exporta `ALL_MODULE_KEYS` y `ModuleKey` — los permisos se sincronizan solos |
| `AuthContext.tsx` | Importa `ModuleKey` en vez de tener interfaz escrita a mano |
| `supabase.ts` | Errores descriptivos con `❌`/`⚠️` + nuevas funciones de totales |
| Reportes (todas_las_op, ventas-tv) | Lazy load, límite 100 registros, totales via RPC, tipado `IOpRecord` |

### Política de UX aplicada: "Zero-Load Initial"
- La tabla no carga al abrir → página instantánea
- El usuario elige filtros → presiona BUSCAR → recibe 100 registros
- El contador de total real viene del servidor vía RPC (no de los 100 descargados)
