# 🚀 Plan de Saldos Recontra Reales — Telesol

## 1. El Objetivo Máximo
Lograr que el Portal muestre la **Verdad Administrativa Total**, incluyendo deudas que PowerBI actualmente ignora (órdenes facturadas pero sin pagos iniciales). El objetivo es que el Saldo Pendiente del Portal ($119M) sea la herramienta de gestión principal.

## 2. Nueva Arquitectura de Datos
Actualmente, el saldo se calcula al vuelo (on-the-fly) o se toma de la tabla histórica de pagos. Vamos a pasar a un modelo de **Campo Persistente**:

*   **Tabla `ordenes_publicidad`**: 
    *   Se agregará la columna `saldo_actual` (decimal).
    *   **Lógica Inicial**: Todo registro nuevo nace con `saldo_actual = importe_total`.
*   **Trigger en `pagos`**: 
    *   Se creará un disparador SQL que detecte cuando entra un pago.
    *   Automáticamente restará el monto del pago de la OP correspondiente.
    *   **NO se modificará** la lógica actual de ingresos de pagos ni el saldo histórico en la tabla `pagos`.

## 3. Resolución de Bugs Pendientes
### 🔴 Error: No se pueden eliminar OPs cargadas
*   **Síntoma**: Al intentar borrar una OP desde la pantalla de "Carga de OP", el sistema no lo permite.
*   **Causa**: Restricción de integridad referencial. La OP tiene registros hijos en `unidades_negocio`, `tv` o `pagos`.
*   **Solución**:
    1.  Implementar "ON DELETE CASCADE" en la base de datos para que al borrar una OP se limpien sus hijos automáticamente (solo para usuarios Administradores).
    2.  Habilitar el botón de eliminación en el frontend con una doble confirmación de seguridad.

## 4. Auditoría de Datos
*   Se mantendrá el script `audit_payments_amounts.py` para comparar el total de pagos contra SharePoint periódicamente.
*   Se creará un reporte de consistencia donde:
    `Suma(Pagos) + Saldo Actual == Importe Total`. Si esto no da cero, el sistema marcará una alerta roja.

---

**Estado:** Pendiente de Iniciación SQL.
**Fecha:** 16 de Abril 2026
