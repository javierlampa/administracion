# 📘 Sistema Telesol — Estado del Proyecto y Arquitectura

> **Última actualización:** 14 de Abril 2026  
> **Estado general:** ✅ Portal activo | ✅ Paridad de datos Enero/Febrero SOLUCIONADA | 🤖 Bot WhatsApp V3 estable

---

## 🏗️ Arquitectura General

```
SharePoint (Fuente de Verdad Legado)
        ↓ sharepoint_sync.py        → Incremental cada 1h (Lunes-Viernes 8-16hs)
        ↓ full_sync.py              → Espejo total de unidades_negocio desde SharePoint (NUEVO)
        ↓ fast_upload_ops.py        → Sincroniza ordenes_publicidad desde el CSV maestro local
Supabase (PostgreSQL)
        ↓ Vistas SQL (v_*)          → Cruzan tablas y calculan saldos
        ↓ Funciones RPC (get_*)     → Totales y KPIs empaquetados en un solo request
Portal Next.js (portal/)
        → Todos los módulos de gestión y reporte
Bot WhatsApp (whatsapp_bot.py)
        → FastAPI en puerto 3001, conectado a Evolution API v2
```

---

## 🗄️ Base de Datos: Tablas Principales

| Tabla | Descripción | Fuente |
|---|---|---|
| `ordenes_publicidad` | Tabla maestra de órdenes de publicidad | SharePoint / CSV |
| `unidades_negocio` | Una fila por unidad de negocio de cada OP | SharePoint |
| `tv` | Datos técnicos TV/Radio/Digital de cada pauta | SharePoint |
| `pagos` | Pagos y cobros de cada orden | SharePoint |
| `clientes` | Maestro de clientes | SharePoint |
| `vendedores` | Maestro de vendedores | SharePoint |
| `programas` | Maestro de programas | SharePoint |
| `perfiles` | Usuarios del portal con permisos y roles | Supabase Auth |
| `bot_sesiones` | Estado de sesión de cada usuario de WhatsApp | Bot |
| `bot_interacciones` | Log de mensajes entrantes/salientes | Bot |

### Campos clave en `unidades_negocio`

| Campo | Tipo | Descripción |
|---|---|---|
| `op_id` | UUID FK | Referencia a `ordenes_publicidad.id`. Puede ser NULL si la OP no tiene fecha en el sistema |
| `op_numero` | TEXT | Número de OP tal como viene de SharePoint |
| `unidad_negocio` | TEXT | Nombre de la unidad: "Canal Telesol", "Radio 1020", etc. |
| `importe_total` | FLOAT | Importe de esa unidad de negocio para esa OP |

---

## 🔭 Vistas SQL (Motor de Reportes)

| Vista | Módulo | Qué calcula |
|---|---|---|
| `v_todas_las_op_report` | Todas las OP | Junta OP+Cliente+Vendedor, calcula `saldo_actual` |
| `v_reporte_programas` | Ventas TV | Detalle cruzado de pauta TV/Radio con datos OP |
| `v_dashboard_ranking_tv` | Dashboard | Ranking de facturación + KPIs |
| `v_pagos_resumen` | Pagos | Resumen de pagos y saldos por OP |
| `v_comisiones_report` | Comisiones | Analítico de pagos + vendedor + cliente |

---

## ⚡ Funciones RPC en Supabase

> Las funciones RPC son la manera más eficiente de calcular datos complejos: en lugar de mandar 3 pedidos desde la web, mandan 1 solo y Supabase devuelve todo empaquetado. **No tocan ni rompen las vistas existentes.**

| Función | Descripción |
|---|---|
| `fetch_sum_kpis(year, month)` | KPIs del Dashboard (total facturado, cobrado, saldo) |
| `get_report_totals(...)` | Totales de Todas las OP con todos los filtros activos |
| `get_ventas_tv_totals(...)` | Totales de Ventas TV con todos los filtros activos |
| `atomic_save_op(...)` | Guardado atómico de una OP completa (cabecera + bloques) |
| `get_monitoring_report(date, unit)` | Pautas del día para Monitoreo de Aire |
| `get_kpi_resolver(...)` | KPIs de facturación para el Dashboard |
| `get_evolucion_tc_metrics()` | Datos para reporte "Evolución por Tipo de Cliente" |
| `get_evolucion_un_metrics(p_start_date, p_end_date)` | **NUEVO** — Datos para reporte "Evolución por Unidad de Negocio" |

---

## 🖥️ Portal Next.js: Módulos

| Ruta | Módulo | Estado |
|---|---|---|
| `/reportes/inicio_dash` | Dashboard principal con KPIs y ranking | ✅ Activo |
| `/reportes/todas_las_op` | Reporte maestro de órdenes de publicidad | ✅ Activo |
| `/reportes/evolucion_tc` | Evolución de Ventas por Tipo de Cliente | ✅ Activo |
| `/reportes/evolucion_un` | **NUEVO** Evolución por Unidad de Negocio | ⚠️ Activo pero con datos incorrectos |
| `/reportes/ventas-tv` | Grilla técnica de pautas TV y Radio | ✅ Activo |
| `/reportes/comisiones` | Reporte de comisiones por vendedor | ✅ Activo |
| `/reportes/pagos` | Pagos y saldos por OP | ✅ Activo |
| `/gestion/lista-op` | Listado y búsqueda de OPs | ✅ Activo |
| `/gestion/carga-op` | Alta y edición de Órdenes de Publicidad | ✅ Activo |
| `/gestion/monitoreo` | Monitoreo de pautas en aire | ✅ Activo |
| `/gestion/pagos-carga` | Carga de pagos y cobros | ✅ Activo |
| `/gestion/comisiones-liquidar` | Liquidación de comisiones | ✅ Activo |
| `/administracion/clientes` | Base de clientes | ✅ Activo |
| `/administracion/vendedores` | Base de vendedores | ✅ Activo |
| `/administracion/programas` | Base de programas | ✅ Activo |
| `/admin/usuarios` | Gestión de usuarios + WhatsApp bot | ✅ Activo |

---

4. **Gráfico Pastel #2** — Número de órdenes por tipo de cliente

### ¿Cómo funciona?
- El dato `ClasificacionClientes` de SharePoint se guarda en el campo `clasificacion` de `ordenes_publicidad`.
- La función RPC `get_evolucion_tc_metrics()` procesa esos datos y los devuelve en 3 arrays listos para graficar.
- La página React en `/reportes/evolucion_tc/page.tsx` consume el RPC y renderiza los 4 gráficos con colores idénticos a PowerBI.

### Estado actual
- ✅ Función RPC `get_evolucion_tc_metrics()` creada en Supabase
- ✅ Campo `clasificacion` mapeado en ambos scripts de sincronización
- ✅ Página React armada y conectada al RPC
- ✅ Menú lateral actualizado con el link al nuevo reporte
- ⏳ Pendiente: Ejecutar `sharepoint_full_sync.py` exitosamente para poblar los datos

---

## 🔒 Permisos (RLS - Row Level Security)

> **Problema resuelto en esta sesión:** El botón de Eliminar OP no funcionaba desde la web porque las tablas tenían ROW LEVEL SECURITY activo bloqueando el DELETE del usuario anónimo.

**Solución:** Ejecutar el archivo `fix_delete_permissions.sql` en Supabase SQL Editor:
```sql
ALTER TABLE ordenes_publicidad DISABLE ROW LEVEL SECURITY;
ALTER TABLE unidades_negocio DISABLE ROW LEVEL SECURITY;
ALTER TABLE tv DISABLE ROW LEVEL SECURITY;
ALTER TABLE pagos DISABLE ROW LEVEL SECURITY;
```

---

## 🤖 Bot WhatsApp — Estado Actual (V3)

> **Archivo:** `whatsapp_bot.py` — FastAPI en puerto `3001`  
> **Integración:** Evolution API v2, instancia `agente_whatsapp_765694`

### Estados implementados

| Estado | Descripción |
|---|---|
| `ROOT` | Menú inicial: elegir entre Clientes o Vendedores |
| `WAITING_NAME` | Espera que el usuario escriba el nombre a buscar |
| `WAITING_CONFIRM` | Confirma si la entidad encontrada es la correcta |
| `MENU_ACTIVE` | Menú de acciones específicas (saldo, pauta, OPs, PDF/Excel) |

### 🐛 Bug pendiente: Envío de PDF/Excel por WhatsApp

**Síntoma:** Evolution API devuelve `400 - "Owned media must be a url or base64"` al enviar archivos.  
**Causa:** El campo `media` del payload debe recibir **base64 puro**, sin prefijo `data:mime/type;base64,`.  
**Estado:** Corrección aplicada pero pendiente de confirmar en producción.

---

## ⚙️ Configuración y Arranque

**Variables en `.env`:**
```
SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_URL
SP_TENANT_ID, SP_CLIENT_ID, SP_CLIENT_SECRET
NEXT_PUBLIC_EVO_URL (ej: http://192.168.1.187:1611)
EVO_API_KEY, EVO_INSTANCE
GEMINI_API_KEY
```

**Arrancar todo:**
```bash
cd portal
npm run dev:all
```
→ Levanta Next.js en puerto 3000 y el bot Python en puerto 3001.

**Sincronización manual completa (limpia todo y re-descarga):**
```bash
python sharepoint_full_sync.py
```

**Sincronización incremental (solo los cambios recientes):**
```bash
python sharepoint_sync.py
```

---

## 🚀 Próximos Pasos (en orden de prioridad)

1. ⏳ **Poblar campo `clasificacion`** — Ejecutar sync completo exitosamente
2. ⬜ **Verificar gráfico Evolución TC** — Confirmar que los datos aparecen correctamente  
3. ⬜ **Confirmar envío de PDF/Excel bot** — Bug de base64 pendiente confirmar
4. ⬜ **Pauta de hoy para Vendedor** — Filtro por `vendedor_nombre` en v_todas_las_op_report
5. ⬜ **Resumen de ventas Vendedor** — Opción 3 del menú bot, implementar lógica real
6. ⬜ **Paginación en el portal** — Botón "Cargar más" cuando supere 100 registros
