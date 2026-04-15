# Plan Maestro: Super Agente WhatsApp con Navegación por Estados (V3)

> **Estado:** ✅ IMPLEMENTADO — 13 de Abril 2026

Este plan transformó el bot de WhatsApp en un asistente estructurado y profesional, priorizando la precisión de los datos y la facilidad de uso mediante menús claros, eliminando la dependencia de la IA para el flujo de conversación.

---

## 1. Mapa de Estados y Transiciones

```
Usuario escribe "hola" / "inicio"
        ↓
    [ROOT]  →  "¿Qué deseas consultar?"
        ↓
   [1] CLIENTE          [2] VENDEDOR
        ↓                    ↓
  [WAITING_NAME] ←───────────┘
    "Escribí el nombre..."
        ↓ (busca en DB filtrando por tipo)
  [WAITING_CONFIRM]
    "¿Te referís a XYZ?"
    [1] Sí → [MENU_ACTIVE]   [2] No → [WAITING_NAME]
        ↓
  [MENU_ACTIVE]
    Opciones específicas por rol
    [0] Volver al inicio
```

| Estado | Descripción | Transición |
|:---|:---|:---|
| `ROOT` | Menú: ¿Consultar [1] Clientes o [2] Vendedores? | → `WAITING_NAME` |
| `WAITING_NAME` | Escribe nombre a buscar | Busca en DB por tipo → `WAITING_CONFIRM` |
| `WAITING_CONFIRM` | Confirma si la entidad es correcta | [1] Sí → `MENU_ACTIVE` / [2] No → `WAITING_NAME` |
| `MENU_ACTIVE` | Menú de acciones por rol (Saldo, PDF, etc.) | Ejecuta acción y vuelve al menú |

---

## 2. Gestión de Sesión (Tabla `bot_sesiones` en Supabase)

Campos relevantes:
- `estado`: `ROOT`, `WAITING_NAME`, `WAITING_CONFIRM`, `MENU_ACTIVE`
- `datos_pago` (JSON): contiene `entidad_tipo`, `entidad_temp`, `entidad_confirmada`
- `numero`: número de teléfono del usuario (PK)

Comandos globales (en cualquier estado):
- `"inicio"`, `"reset"`, `"hola"` → limpia la sesión y vuelve a ROOT

---

## 3. Estructura del Código (`whatsapp_bot.py`)

```
webhook()  →  dispatcher por estado
    ├── handle_root_state()
    ├── handle_waiting_name_state()
    ├── handle_waiting_confirm_state()
    └── handle_menu_active_state()
            ├── [CLIENTE]
            │     1. consultar_saldo_real()
            │     2. consultar_pauta_hoy(entidad, "CLIENTE")
            │     3. buscar_datos_sistema(entidad, "CLIENTE")
            │     4. generar_reporte_pdf(entidad) + send_whatsapp_media()
            └── [VENDEDOR]
                  1. consultar_comisiones_vendedor()
                  2. buscar_datos_sistema(entidad, "VENDEDOR")
                  3. (resumen ventas - pendiente lógica real)
                  4. generar_reporte_excel() + send_whatsapp_media()
```

---

## 4. Menús Implementados

### Menú Inicial (ROOT)
```
¿Qué deseas consultar hoy? 🤔
[1] 👤 Por Cliente
[2] 💼 Por Vendedor
```

### Menú CLIENTE activo
```
OPCIONES DE CLIENTE 👤
[1] 💰 Consultar Mi Saldo
[2] 📺 Mi Pauta de Hoy
[3] 📂 Ver Mis Órdenes (OPs)
[4] 📥 Descargar Estado de Cuenta (PDF)
[0] 🔙 Cambiar Consulta / Inicio
```

### Menú VENDEDOR activo
```
OPCIONES DE VENDEDOR 💼
[1] 💵 Mis Comisiones
[2] 👥 Saldos de Mis Clientes
[3] 📈 Resumen de Ventas
[4] 📄 Descargar Reporte de Gestión (Excel)
[0] 🔙 Cambiar Consulta / Inicio
```

---

## 5. Ventajas de la V3

1. **Cero errores de "adivinanza":** Al confirmar el nombre, eliminamos el riesgo de mezclar datos.
2. **Interfaz profesional:** Botones numerados [1], [2] fáciles de usar en WhatsApp.
3. **Control total:** "inicio" resetea todo en cualquier momento.
4. **Resiliencia sin IA:** Si Gemini falla, el bot sigue funcionando con código puro.
5. **Memoria de sesión:** El bot recuerda de quién estás hablando hasta que resetees.

---

## 6. Bugs Conocidos y Resueltos en esta Sesión

| Bug | Causa | Solución |
|---|---|---|
| Bot saltaba al menú de Cliente sin preguntar | El proceso no se había reiniciado con el nuevo código | Reiniciar `npm run dev:all` |
| "Pauta de hoy" no mostraba nada | La función no filtraba por entidad y no tenía mensaje de "no hay resultados" | Actualizada `consultar_pauta_hoy(entidad, tipo)` |
| PDF no se generaba — "Not enough horizontal space" | fpdf2 deprecó la API de `txt=`, `ln=True` | Actualizado a sintaxis moderna de fpdf2 |
| PDF no se enviaba — `400 Bad Request` | Evolution API v2 no acepta prefijo `data:mime;base64,` | Se envía base64 puro sin prefijo |

---

## 7. Pendientes

- [ ] Confirmar que el envío de PDF/Excel funcione end-to-end
- [ ] Implementar lógica real para "Resumen de Ventas" del vendedor (opción 3)
- [ ] Agregar filtro de pauta por vendedor en el menú de VENDEDOR (opción pendiente)
