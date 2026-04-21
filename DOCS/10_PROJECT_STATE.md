# 📘 Sistema Telesol — Estado del Proyecto y Arquitectura

> **Última actualización:** 20 de Abril 2026  
> **Estado general:** ✅ Portal activo | ✅ PARIDAD FINANCIERA TOTAL (OP vs TV = $0 de diferencia) | ✅ Sync Mirror con deduplicación SP_ID | 🤖 Bot WhatsApp V3

---

## 🏗️ Arquitectura General

```
SharePoint (Fuente de Verdad de Gestión)
        ↓ sharepoint_sync.py        → Sincroniza OPs, Pagos y Técnicos.
Supabase (PostgreSQL - LA VERDAD TOTAL)
        ↓ v_todas_las_op_report     → Vista unificada de órdenes con SALDO REAL.
        ↓ Trigger TR_SALDO          → Actualiza saldo_actual en OPs al recibir un pago.
Portal Next.js (portal/)
        → Dashboard con $108M de diferencia detectada y explicada como Deuda Real.
Bot WhatsApp (whatsapp_bot.py)
        → Consultas de saldos en tiempo real usando el nuevo modelo de Saldo Actual.
```

---

## ✅ Reconciliación Financiera — COMPLETADA 20/04/2026

### Resultado Final
- **Total OP Maestras (2026):** $242.019.894,16
- **Total Tabla TV (2026):** $242.019.894,16
- **DIFERENCIA:** $0,00 ✅

### Qué se hizo
1. Se corrigió la fuente de datos de TV (se cambia de lista `Tipo de Publicidad` a lista `TV`).
2. Se implementó deduplicación por `SP_ID` interno de SharePoint para evitar clones fantasma.
3. Se agregaron campos faltantes: `iva`, `importe_sin_iva`, `programa_id` al mapper de TV.
4. Se auditaron OP vs TV con `check_missing_tv.py` y `generate_report.py`, detectando 15 OPs con diferencias de monto.
5. El usuario corrigió manualmente en SharePoint y se volvió a sincronizar hasta llegar a diferencia $0.

---

## 🗄️ Base de Datos: Tablas Principales

| Tabla | Descripción | Fuente |
|---|---|---|
| `ordenes_publicidad` | Maestro de órdenes con campo `saldo_actual` | SharePoint / CSV |
| `unidades_negocio` | Una fila por unidad de negocio de cada OP | SharePoint |
| `tv` | Datos técnicos TV/Radio/Digital de cada pauta | SharePoint |
| `pagos` | Registro histórico de cobros (Fuente para el descuento) | SharePoint |
| `clientes` | Maestro de clientes | SharePoint |
| `vendedores` | Maestro de vendedores | SharePoint |
| `programas` | Maestro de programas | SharePoint |
| `perfiles` | Usuarios del portal con permisos y roles | Supabase Auth |
| `bot_sesiones` | Estado de sesión de cada usuario de WhatsApp | Bot |
| `bot_interacciones` | Log de mensajes entrantes/salientes | Bot |

---

## ⚡ Funciones RPC en Supabase

| Función | Descripción |
|---|---|
| `fetch_sum_kpis(year, month)` | KPIs del Dashboard (total facturado, cobrado, saldo) |
| `get_report_totals(...)` | Totales de Todas las OP con todos los filtros activos |
| `get_ventas_tv_totals(...)` | Totales de Ventas TV con todos los filtros activos |
| `atomic_save_op(...)` | Guardado atómico de una OP completa (cabecera + bloques) |

---

## 🚀 Próximos Pasos Prioritarios

1.  🔴 **FIX: Eliminación de OP**: Implementar `ON DELETE CASCADE` en FK de tablas hijas (`tv`, `pagos`, `unidades_negocio`) para habilitar borrado fluido de OPs desde el portal.
2.  🟡 **Banner Digital**: Verificar el cálculo y campo de "Ventas Tipo de Banner Digital" en `ordenes_publicidad` (no está en la tabla `tv`).
3.  🟡 **Bug WhatsApp RLS**: Resolver bug de guardado del campo `numero_celular` en `/admin/usuarios` (posible política RLS en Supabase).
4.  🟢 **Monitoreo**: Ejecutar `generate_report.py` periódicamente para detectar nuevas discrepancias antes de que acumulen.
5.  ⬜ **Confirmar envío PDF/Excel bot**: Bug de base64 pendiente confirmar en producción.
