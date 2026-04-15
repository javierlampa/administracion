# 🤖 Contexto de Trabajo — Bot WhatsApp + Portal Telesol

> **Fecha:** 13 de Abril 2026  
> **Sesión activa:** Implementación Bot V3 con navegación por estados

---

## ¿Qué es este proyecto?

Sistema de administración interno para una empresa de medios (TV/Radio). Tiene dos partes:

1. **Portal Web (Next.js)** — Gestión de órdenes de publicidad, clientes, vendedores, reportes, comisiones, etc.
2. **Bot de WhatsApp** — Permite a clientes y vendedores consultar su información directamente desde WhatsApp sin entrar al portal.

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Frontend | Next.js 14 (TypeScript) |
| Base de datos | Supabase (PostgreSQL) |
| Bot WhatsApp | Python 3 (FastAPI) |
| Mensajería | Evolution API v2 (auto-hospedado en red local) |
| IA (opcional) | Google Gemini (fallback cuando no está disponible) |
| Reportes | fpdf2 (PDF), openpyxl/pandas (Excel) |

**Arranque del sistema:**
```bash
cd "F:\JAVIER PRIVADO\APP PHYTON\ADMINISTRACION\portal"
npm run dev:all
```
→ Portal en `http://localhost:3000`, Bot en `http://localhost:3001`

---

## Qué estuvimos haciendo en esta sesión

### Objetivo: Refactorizar el Bot a V3 (Navegación por Estados)

El bot viejo dependía de la IA (Gemini) para interpretar los mensajes, lo que causaba respuestas imprecisas y mezcla de datos. La V3 implementa una **máquina de estados** que guía al usuario por un flujo predecible.

---

## Flujo de conversación implementado

```
Usuario: "hola"
Bot: "¿Qué deseas consultar? [1] Cliente [2] Vendedor"

Usuario: "1"
Bot: "Escribí el nombre del cliente:"

Usuario: "cafe america"
Bot: "¿Te referís a CAFE AMERICA S.A.? [1] Sí [2] No"

Usuario: "1"
Bot: "✅ Confirmado! Opciones para CAFE AMERICA S.A.:
      [1] Saldo  [2] Pauta hoy  [3] Ver OPs  [4] PDF  [0] Inicio"

Usuario: "4"
Bot: "Preparando PDF..." → Envía archivo PDF
```

---

## Historial de bugs resueltos en esta sesión

### 1️⃣ El bot iba directo al menú de "Clientes" sin preguntar
**Causa:** El proceso de Python no se había reiniciado — seguía corriendo el código viejo.  
**Solución:** Reiniciar con Ctrl+C y `npm run dev:all`.

### 2️⃣ "Mi Pauta de Hoy" no mostraba nada y ponía el menú solo
**Causa:** La función `consultar_pauta_hoy()` no filtraba por entidad y no retornaba un mensaje cuando no había resultados.  
**Solución:** Actualizada como `consultar_pauta_hoy(entidad, tipo)`, con mensaje "No hay pautas activas para hoy para [entidad]" cuando no hay datos.

### 3️⃣ PDF no se generaba — "Not enough horizontal space"
**Causa:** La librería `fpdf2` (versión nueva) deprecó parámetros como `txt=`, `ln=True`. El ancho de celda `200` chocaba con los márgenes.  
**Solución:** Actualizado a sintaxis moderna:
```python
pdf.cell(0, 10, text="...", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.multi_cell(0, 8, text="...", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
```

### 4️⃣ PDF no se enviaba — `400 Bad Request` de Evolution API
**Error exacto:**
```json
{"message": ["Owned media must be a url or base64"]}
```
**Causa 1 (resuelta):** El campo del payload era `base64` — debía ser `media`.  
**Causa 2 (resuelta):** Evolution API v2 espera **base64 puro**, sin el prefijo `data:application/pdf;base64,`.

```python
# ❌ Incorrecto
"media": f"data:application/pdf;base64,{base64_data}"

# ✅ Correcto
"media": base64_data  # solo el string base64, sin prefijo
```

**Estado:** Corrección aplicada — pendiente confirmación en producción.

---

## Archivos clave del bot

| Archivo | Descripción |
|---|---|
| `whatsapp_bot.py` | Archivo principal del bot |
| `.env` | Variables de entorno (Supabase, EVO API, Gemini) |
| `requirements.txt` | Dependencias Python |
| `DOCS/implementation_plan_v3.md` | Plan técnico de la V3 |
| `DOCS/10_PROJECT_STATE.md` | Estado general del sistema |

---

## Variables de entorno del bot (`.env`)

```
SUPABASE_URL=...
SUPABASE_KEY=...
NEXT_PUBLIC_EVO_URL=http://192.168.1.187:1611
EVO_API_KEY=...
EVO_INSTANCE=agente_whatsapp_765694
GEMINI_API_KEY=...
```

---

## Qué sigue pendiente

1. **Confirmar que el PDF llega al chat de WhatsApp** — El fix del base64 debería resolverlo.
2. **Resumen de Ventas (Opción 3 del Vendedor)** — No tiene lógica real todavía, solo muestra un mensaje placeholder.
3. **Excel para Vendedor** — La función `generar_reporte_excel()` necesita revisión similar al PDF.
4. **Pauta de hoy para Vendedor** — Se podría agregar como opción 5 en el menú de Vendedor.

---

## Notas de arquitectura importantes

- La tabla `bot_sesiones` en Supabase persiste el estado entre mensajes.
- El campo `datos_pago` (JSON) almacena: `entidad_tipo`, `entidad_temp`, `entidad_confirmada`.
- La función `buscar_datos_sistema(texto, tipo)` filtra por CLIENTE o VENDEDOR según el tipo elegido.
- `send_whatsapp_media()` envía PDFs y Excels — usa base64 puro sin prefijo.
- Gemini solo se usa opcionalmente — el bot funciona sin IA gracias a la máquina de estados.
