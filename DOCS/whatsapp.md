# Integración WhatsApp (WAHA) — Estado al 08/04/2026

## ✅ Infraestructura de Base de Datos (COMPLETO)

La tabla `perfiles` ya tiene los campos necesarios:
- `numero_celular` (text) — Número en formato internacional sin `+` ni espacios (ej: `5491155556666`)
- `whatsapp_habilitado` (boolean, default: false) — Interruptor por usuario

## ✅ Panel de Administración (COMPLETO — con bug pendiente)

La pantalla `/admin/usuarios` ya tiene:
- Campo de número celular con ícono de teléfono
- Toggle visual verde "Habilitado para el Bot"
- Ícono `💬 WA` en el listado para identificar usuarios habilitados
- El SELECT ya carga `numero_celular` y `whatsapp_habilitado` al editar

## 🐛 BUG ACTIVO: El número no se guarda desde el portal

**Síntoma:** "¡Guardado correctamente!" pero `numero_celular` queda NULL.  
**SQL directo funciona:** Confirmado que la columna acepta datos.  
**No hay triggers:** Verificado — no hay triggers en `perfiles`.  
**Causa probable:** Política RLS bloquea el UPDATE silenciosamente.

### Solución Opción A — Política RLS (Recomendada, sin cambios de código)
```sql
-- Ejecutar en Supabase SQL Editor
CREATE POLICY "admin_can_update_all_profiles"
ON perfiles FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM perfiles p
        JOIN roles r ON p.role_id = r.id  
        WHERE p.id = auth.uid() AND r.nombre = 'ADMIN'
    )
);
```

### Solución Opción B — Service Role Key (Bypass completo de RLS)
1. Ir a Supabase → Project Settings → API → copiar `service_role` secret
2. Agregar a `.env`: `SUPABASE_SERVICE_ROLE_KEY=eyJ...`
3. Crear `src/lib/supabaseAdmin.ts` con cliente que bypasea RLS
4. Cambiar el UPDATE en `admin/usuarios/page.tsx` para usar `supabaseAdmin`

---

## ⏳ Próximos Pasos del Bot (Después de resolver el bug)

### Paso 3: Script del Bot WAHA
Crear `whatsapp_bot.py` o `whatsapp_bot.js` que:
1. Expone un endpoint webhook en puerto `3001`
2. Recibe mensajes entrantes de WAHA
3. Consulta `perfiles` para verificar si el número está en whitelist (`whatsapp_habilitado = true`)
4. Si no está habilitado → `return` sin responder (anti-baneo)
5. Implementa delay de 2-4 segundos + señal "escribiendo..." antes de responder
6. Responde consultas sobre OPs, saldos o pautas del día consultando Supabase

### Comandos del Bot Planificados
| Comando | Respuesta |
|---|---|
| `saldo [nombre cliente]` | Saldo pendiente de ese cliente |
| `op [número]` | Estado de una OP específica |
| `hoy` | Pautas que inician o terminan hoy |
| `ranking` | Top 5 clientes del mes |

### Seguridad Anti-Baneo
- Máximo 10 números en whitelist
- Delay variable 2-4 segundos antes de responder
- Señal "escribiendo..." activada antes de cada respuesta
- Sesión persistente (keep-alive) para no re-escanear QR

---

## 🔑 Credenciales WAHA
Verificar en el servidor Ubuntu:
- WAHA corriendo en `http://[SERVER_IP]:3000`
- Instancia creada con nombre a confirmar
- QR escaneado o pendiente de escanear
