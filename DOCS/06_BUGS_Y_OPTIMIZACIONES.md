# 06 — Bugs, Optimizaciones y Deuda Técnica

> **Última actualización:** 15 de Abril 2026

---

## ✅ RESUELTOS — Sesión 15/04/2026 (Sync Incremental Robusto)

### `sharepoint_sync.py` se detenía ante el primer error de duplicado
- **Síntoma:** Error `23505 duplicate key value violates unique constraint "ordenes_publicidad_op_key"` detenía todo el proceso
- **Causa:** El upsert se hacía en lote; un solo conflicto de clave rompía el batch entero
- **Solución:** Upsert individual por registro con `try/except` granular. Los errores se anotan y el proceso continúa

### `sharepoint_sync.py` no distinguía entre ID interno y número de OP real
- **Síntoma:** La OP `7291` con `op_id` diferente tiraba error `unique_op_un` en `unidades_negocio`
- **Causa:** La validación de duplicados usaba el ID interno del sistema en lugar del número de OP real
- **Solución:** La validación ahora usa el campo `op_numero` (el número real de la OP) como criterio de unicidad

### Reportes de error no daban información suficiente
- **Síntoma:** `reporte_huerfanos.txt` era un solo archivo con formato inconsistente
- **Solución:** Reemplazado por dos archivos separados:
  - `sincronizacion_exitosa.txt` — OPs actualizadas, agrupadas por tabla
  - `sincronizacion_errores.txt` — Errores con Lista, OP (número real), SP_ID y motivo exacto

### Contadores en consola mostraban números negativos
- **Síntoma:** `-3 salteados/error` en la salida de consola
- **Causa:** `count_success` no se inicializaba antes del loop de tablas relacionadas
- **Solución:** `count_success = 0` inicializado correctamente al comienzo de cada iteración de tabla

---

## ✅ RESUELTOS — Sesión 14/04/2026 (Paridad Datos Enero/Febrero SOLUCIONADA)

### `unidades_negocio` mostraba valores incorrectos en Enero y Febrero
- **Causa 1 — API de Supabase limita el DELETE a 1000 filas a la vez:** Al intentar vaciar la tabla con `.delete().neq('op_numero', '0')`, la API borraba solo las primeras 1000 filas y dejaba el resto intacto. La siguiente inserción apilaba registros nuevos sobre los que quedaban.
- **Causa 2 — Claves de campo incorrectas en SharePoint Graph API:** `full_sync.py` usaba nombres incorrectos para los campos (`Unidad_x0020_de_x0020_Negocio`, `Importe_x0020_Total`) cuando los nombres reales son `Unidaddenegocio0` e `ImporteTotal`. Esto causaba que se insertaran filas con `unidad_negocio = NULL` e `importe_total = 0`.
- **Causa 3 — pandas convierte None a float NaN:** Al usar pandas para deduplicar, los valores `None` se convertían a `float('nan')`, que no es serializable como JSON por Supabase y tiraba error en lotes enteros de 500.
- **Causa 4 — Pérdida de dinero por des-duplicación destructiva (LA CAUSA FINAL):** En SharePoint había 9 registros duplicados legítimos ocultos o sucios donde una misma OP tenía varías líneas con la misma Unidad de Negocio (ej. Digital Telesol repetido). La lógica en Python simplemente borraba el segundo registro, perdiendo esa plata de la suma total.
- **Solución final:**
  - `wipe_table.py` — Bucle que borra de a 1000 hasta confirmar 0 filas restantes.
  - `full_sync.py` — Actualizado para aplicar una **fusión acumulativa (suma)** cuando detecta un duplicado sucio de la misma unidad en la misma OP.
- **Estado:** ✅ Las tablas en Next.js ahora coinciden al centavo con el total de PowerBI de Enero y Febrero (Paridad Lograda).

### `parse_num()` devolvía `float('nan')` rompiendo JSON
- **Causa:** Cuando SharePoint devolvía `None` para un campo numérico, el cast a `float()` generaba `nan`
- **Solución:** Agregado `if math.isnan(num): return 0.0` en `parse_num()` de `full_sync.py`

---

## ✅ RESUELTOS — Sesión 13/04/2026 (Bot WhatsApp V3)


### Bot saltaba al menú de Cliente sin preguntar el tipo
- **Causa:** El proceso Python no se había reiniciado — ejecutaba código viejo en memoria
- **Solución:** Reiniciar `npm run dev:all` después de cada cambio en `whatsapp_bot.py`

### "Mi Pauta de Hoy" no mostraba resultados y devolvía el menú vacío
- **Causa:** `consultar_pauta_hoy()` no filtraba por entidad y no tenía mensaje de "sin resultados"
- **Solución:** Refactorizada como `consultar_pauta_hoy(entidad, tipo)` con filtro por `cliente_nombre_comercial` o `vendedor_nombre` y mensaje explícito cuando no hay datos
- **Archivo:** `whatsapp_bot.py`

### PDF no se generaba — "Not enough horizontal space"
- **Causa:** `fpdf2` v2.7+ deprecó `txt=`, `ln=True` y ancho fijo `200`
- **Solución:** Actualizado a sintaxis moderna:
  ```python
  from fpdf.enums import XPos, YPos
  pdf.cell(0, 10, text="...", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
  pdf.multi_cell(0, 8, text="...", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
  ```
- **Archivo:** `whatsapp_bot.py` → `generar_reporte_pdf()`

### PDF no se enviaba — `400 Bad Request` de Evolution API
- **Error exacto:** `{"message": ["Owned media must be a url or base64"]}`
- **Causa 1:** Payload usaba clave `base64` — Evolution API v2 requiere `media`
- **Causa 2:** El valor incluía prefijo `data:application/pdf;base64,...` — la API requiere base64 puro sin prefijo
- **Solución:**
  ```python
  # ❌ Incorrecto
  payload = {"base64": f"data:application/pdf;base64,{b64}"}
  # ✅ Correcto
  payload = {"media": b64}   # solo el string base64 crudo
  ```
- **Archivo:** `whatsapp_bot.py` → `send_whatsapp_media()`
- **Estado:** Corrección aplicada — pendiente validación final en producción

---

## ✅ RESUELTOS — Sesiones anteriores (Portal Web)

### Errores Silenciosos en Base de Datos
- `catch { return null; }` → ahora tiene `console.error("❌ ...")` descriptivo
- **Archivo:** `src/lib/supabase.ts`

### Carga Masiva de Datos en el Navegador
- 500 filas con `.reduce()` en el browser → sumatorias vía RPC en Supabase
- **RPCs:** `get_report_totals`, `get_ventas_tv_totals`

### Interface `UserPermissions` Duplicada
- `ModuleKey` se genera desde `menuConfig.ts` — `AuthContext.tsx` lo importa

### Tipado `any` en Datos Críticos
- `useState<any[]>` → `useState<IOpRecord[]>` — compilador avisa errores

### Página Raíz Vacía
- `/` ahora redirige a `/reportes/inicio_dash`

### Contador de Registros Invisible en Modo Oscuro
- `text-slate-900` → `isLight ? 'text-slate-900' : 'text-sky-400'`

### Carga Automática al Abrir Reportes
- Lazy load — tabla vacía hasta que el usuario presiona BUSCAR

### Bug RLS en Gestión de Usuarios (numero_celular)
- UPDATE de `numero_celular` era bloqueado silenciosamente por la política RLS
- Solución: política `admin_can_update_all_profiles` o uso de `supabaseAdmin` con service key

---

## ⚠️ PENDIENTES (Conocidos)

### Lazy Load en Comisiones y Pagos
- Todavía hacen carga automática al abrir
- **Solución:** Mismo patrón que Todas las OP

### Resumen de Ventas (Bot Vendedor opción 3)
- No tiene lógica real, muestra placeholder
- **Solución:** Consultar `v_reporte_programas` filtrando por `vendedor_nombre`

### Excel para Vendedor (Bot opción 4)
- `generar_reporte_excel()` necesita revisión similar al PDF
- **Solución:** Verificar que el base64 se envíe puro y que openpyxl esté instalado

### Ordenamiento de Tabla  
- `ReportTable.tsx` ordena localmente → con >10.000 registros puede congelar el browser
- **Solución futura:** Pasar orden como parámetro a `.order()` de Supabase

### SharePoint Sync — Token Microsoft puede vencer a mitad del proceso
- Si el token expira a mitad de la sincronización, las requests a Graph API fallan silenciosamente
- **Solución futura:** Renovar el token al inicio de cada tabla, o implementar retry con re-autenticación

### Catálogos descargados completos en cada ciclo
- Programas, Vendedores y Clientes se bajan completos en cada ciclo de 1 hora aunque no hayan cambiado
- **Solución futura:** Cachear en archivo local o memoria con TTL de 6-12 horas

### Bot WhatsApp — `MAESTRO_NOMBRES` se pierde al reiniciar
- El caché de nombres está en memoria → si el proceso se reinicia, la primera búsqueda fuzzy siempre va a la DB
- **Impacto:** Bajo (solo el primer request es más lento)
- **Solución futura:** Persistir en archivo JSON o en `bot_sesiones` de Supabase

---

## 📌 Reglas de Código Establecidas

### Para nuevos módulos de reporte (Portal):
```typescript
// 1. Sumatorias SIEMPRE en RPC de Supabase (nunca .reduce())
// 2. Carga SIEMPRE bajo demanda (sin loadData() en useEffect)
// 3. Límite SIEMPRE 100 registros por búsqueda
// 4. Tipado SIEMPRE con IOpRecord (o interface propia en database.ts)
// 5. Colores SIEMPRE con isLight para garantizar contraste en ambos modos
```

### Para el Bot WhatsApp:
```python
# 1. send_whatsapp_media() envía base64 PURO, sin prefijo data:
# 2. Cada handler de estado devuelve SIEMPRE el menú al final
# 3. Si no hay resultados, mandar mensaje explícito (nunca silencio)
# 4. Reiniciar el proceso después de cada cambio en el código
```
