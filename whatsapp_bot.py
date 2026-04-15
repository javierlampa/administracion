import os
import time
import random
import requests
import json
import httpx
import base64
import difflib
from datetime import datetime, timedelta
import google.generativeai as genai
from fastapi import FastAPI, Request
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configuración Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración Evolution API
EVO_URL = os.getenv("NEXT_PUBLIC_EVO_URL")
EVO_KEY = os.getenv("EVO_API_KEY")
EVO_INSTANCE = os.getenv("EVO_INSTANCE")

# --- CONFIGURACIÓN DE IA (GEMINI) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- HERRAMIENTAS DE CONSULTA Y REPORTES ---
import pandas as pd
from fpdf import FPDF
import io
import re

def safe_print(text):
    """Imprime texto de forma segura en Windows."""
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        limpio = text.encode('ascii', 'ignore').decode('ascii')
        print(limpio, flush=True)

def normalizar_texto(texto: str):
    """Quita acentos, comas y signos de puntuación para mejorar la búsqueda."""
    import unicodedata
    # Convertir a minúsculas y quitar acentos
    texto = texto.lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Quitar signos de puntuación y dejar solo letras, números y espacios
    import re
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    return " ".join(texto.split())

def parsear_fechas(texto: str):
    """Intenta extraer un rango de fechas de un texto humano."""
    from datetime import datetime, timedelta
    hoy = datetime.now()
    
    if "este mes" in texto:
        inicio = hoy.replace(day=1)
        return inicio.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")
    elif "mes pasado" in texto:
        primero_este = hoy.replace(day=1)
        ultimo_pasado = primero_este - timedelta(days=1)
        inicio_pasado = ultimo_pasado.replace(day=1)
        return inicio_pasado.strftime("%Y-%m-%d"), ultimo_pasado.strftime("%Y-%m-%d")
    elif "este ano" in texto or "todo el ano" in texto:
        return hoy.strftime("%Y-01-01"), hoy.strftime("%Y-12-31")
    
    import re
    fechas = re.findall(r'(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2})', texto)
    if len(fechas) >= 2:
        try:
            d1 = datetime.strptime(fechas[0], "%d/%m/%Y" if len(fechas[0]) > 8 else "%d/%m/%y")
            d2 = datetime.strptime(fechas[1], "%d/%m/%Y" if len(fechas[1]) > 8 else "%d/%m/%y")
            return d1.strftime("%Y-%m-%d"), d2.strftime("%Y-%m-%d")
        except: pass
    return None, None

def limpiar_nombre(texto: str):
    """Limpia caracteres prohibidos para nombres de archivo."""
    return re.sub(r'[^\w\s-]', '', texto).strip().replace(' ', '_')

def send_whatsapp_media(number: str, base64_data: str, fileName: str, caption: str = ""):
    """Envía un archivo (PDF, Excel, Imagen) por WhatsApp."""
    try:
        url = f"{EVO_URL}/message/sendMedia/{EVO_INSTANCE}"
        
        # Asegurar formato JID
        if "@" not in number:
            jid = f"{number}@s.whatsapp.net"
        else:
            jid = number

        # Determinar mimetype
        is_pdf = fileName.lower().endswith(".pdf")
        mimetype = "application/pdf" if is_pdf else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Limpiar nombre de archivo para evitar errores en Evolution API
        ext = ".pdf" if is_pdf else ".xlsx"
        nombre_limpio = limpiar_nombre(fileName.replace(ext, "")) + ext
        
        payload = {
            "number": jid,
            "media": base64_data,
            "mediatype": "document",
            "mimetype": mimetype,
            "fileName": nombre_limpio,
            "caption": caption
        }
        headers = {"apikey": EVO_KEY, "Content-Type": "application/json"}
        
        safe_print(f"DEBUG: Enviando archivo {nombre_limpio} a {jid}...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code >= 400:
            safe_print(f"DEBUG: ERROR Evolution Media ({response.status_code}): {response.text}")
        else:
            safe_print(f"DEBUG: Éxito enviando archivo (Status {response.status_code})")
            
    except Exception as e:
        safe_print(f"DEBUG: Error fatal enviando media: {e}")

# --- CACHE DE MAESTROS PARA FUZZY SEARCH ---
MAESTRO_NOMBRES = {"clientes": [], "vendedores": [], "last_update": None}

def obtener_maestro_nombres():
    """Obtiene y cachea la lista de todos los nombres de clientes y vendedores."""
    global MAESTRO_NOMBRES
    ahora = datetime.now()
    if MAESTRO_NOMBRES["last_update"] and (ahora - MAESTRO_NOMBRES["last_update"]) < timedelta(minutes=10):
        return MAESTRO_NOMBRES
    
    try:
        safe_print("DEBUG: Actualizando caché de nombres maestros...")
        # Traer clientes (limit 1000 para no saturar, pero cubriendo la mayoría)
        res_c = supabase.table("clientes").select("nombre_comercial").order("nombre_comercial").limit(1000).execute()
        MAESTRO_NOMBRES["clientes"] = [r["nombre_comercial"] for r in (res_c.data or []) if r.get("nombre_comercial")]
        
        # Traer vendedores
        res_v = supabase.table("vendedores").select("nombre").order("nombre").execute()
        MAESTRO_NOMBRES["vendedores"] = [r["nombre"] for r in (res_v.data or []) if r.get("nombre")]
        
        MAESTRO_NOMBRES["last_update"] = ahora
        return MAESTRO_NOMBRES
    except Exception as e:
        safe_print(f"DEBUG: Error actualizando maestros: {e}")
        return MAESTRO_NOMBRES

def buscar_con_fuzzy(texto: str, tipo: str = "CLIENTE"):
    """Busca los nombres más parecidos usando difflib."""
    maestros = obtener_maestro_nombres()
    lista_objetivo = maestros["clientes"] if tipo == "CLIENTE" else maestros["vendedores"]
    
    # get_close_matches devuelve los n mejores resultados (n=3) con un cutoff de similitud
    sugerencias = difflib.get_close_matches(texto.upper(), [n.upper() for n in lista_objetivo], n=3, cutoff=0.5)
    
    # Mapear de vuelta a los nombres originales (capitalización correcta)
    nombres_finales = []
    for s in sugerencias:
        for orig in lista_objetivo:
            if orig.upper() == s:
                nombres_finales.append(orig)
                break
    return nombres_finales

def buscar_datos_sistema(criterio: str, entidad_tipo: str = None, solo_deuda: bool = False, limite: int = 20):
    """Busca en el sistema por un nombre o texto, filtrando opcionalmente por tipo y deuda."""
    try:
        criterio_limpio = criterio.replace(",", "").replace("(", "").replace(")", "").replace("\"", "").strip()
        if not criterio_limpio: return []
        
        safe_print(f"DEBUG: Buscando ({entidad_tipo or 'TODO'}) por: {criterio_limpio} (SoloDeuda={solo_deuda}, Limite={limite})")
        
        query = supabase.table("v_todas_las_op_report").select("*")
        
        # Filtro de deuda si se solicita
        if solo_deuda:
            query = query.gt("saldo_actual", 0)
        
        if entidad_tipo == "CLIENTE":
            query = query.or_(f"cliente_nombre_comercial.ilike.%{criterio_limpio}%,cliente_razon_social.ilike.%{criterio_limpio}%")
        elif entidad_tipo == "VENDEDOR":
            query = query.ilike("vendedor_nombre", f"%{criterio_limpio}%")
        else:
            query = query.or_(f"cliente_nombre_comercial.ilike.%{criterio_limpio}%,cliente_razon_social.ilike.%{criterio_limpio}%,op.ilike.%{criterio_limpio}%,vendedor_nombre.ilike.%{criterio_limpio}%")
            
        res = query.order("fecha_orden", desc=True).limit(limite).execute()
        return res.data if res.data else []
    except Exception as e:
        safe_print(f"DEBUG: Error en buscar_datos_sistema: {e}")
        return []

def consultar_pauta_hoy(entidad: str = None, tipo: str = None):
    """Consulta órdenes con pauta activa hoy, filtrando opcionalmente por cliente o vendedor."""
    try:
        from datetime import datetime
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        query = supabase.table("v_todas_las_op_report").select("op, cliente_nombre_comercial, unidad_negocio, importe_total, inicio_pauta, fin_pauta") \
            .lte("inicio_pauta", hoy).gte("fin_pauta", hoy)
        
        if tipo == "CLIENTE" and entidad:
            query = query.eq("cliente_nombre_comercial", entidad)
        elif tipo == "VENDEDOR" and entidad:
            query = query.eq("vendedor_nombre", entidad)
            
        res = query.execute()
        
        if not res.data:
            return f"No hay pautas activas para hoy para *{entidad or 'todo el sistema'}*."
        
        msg = f"📅 *PAUTA ACTIVA HOY ({entidad or 'General'})*\n"
        for item in res.data[:10]:
            msg += f"• OP {item['op']}: {item['cliente_nombre_comercial']} ({item['unidad_negocio']})\n"
        return msg
    except Exception as e: return f"Error consultando pauta: {str(e)}"

def generar_reporte_excel(query_text: str):
    """Genera un archivo Excel con los datos solicitados y lo devuelve como base64."""
    try:
        data = buscar_datos_sistema(query_text)
        if isinstance(data, str): return data
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte')
        
        excel_pure = base64.b64encode(output.getvalue()).decode()
        return excel_pure
    except Exception as e: return f"Error creando Excel: {str(e)}"

def generar_reporte_pdf(query_text: str):
    """Genera un PDF con SALDOS PENDIENTES (SoloDeuda=True) y hasta 100 registros."""
    try:
        # Petición específica del usuario: Solo deuda y hasta 100 registros
        data = buscar_datos_sistema(query_text, solo_deuda=True, limite=100)
        if not data or isinstance(data, str): return "No hay órdenes con saldo pendiente para este criterio."
        
        # Estilo Portal: Landscape, Colores específicos
        BLUE_COLOR = (37, 99, 235) # Corporate Blue #2563EB
        
        try:
            from fpdf.enums import XPos, YPos
            # Soporte para fpdf2 (Moderno)
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            
            # Encabezado
            pdf.set_font("Helvetica", 'B', 14)
            pdf.set_text_color(*BLUE_COLOR)
            pdf.cell(0, 10, text="REPORTES TELESOL - ESTADO DE CUENTA", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.set_font("Helvetica", 'B', 9)
            pdf.set_text_color(100, 100, 100)
            fecha_str = time.strftime('%d/%m/%Y %H:%M')
            pdf.cell(0, 8, text=f"Consulta: {query_text} | Generado el: {fecha_str}", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)

            # Definición de tabla (Ancho total A4 Landscape ~280mm efectivo)
            cols = [
                ("OP", 15), ("FECHA", 20), ("UNN", 25), ("COMERCIO", 55), 
                ("VENDEDOR", 35), ("INICIO", 20), ("FIN", 20), ("FACTURA", 35), ("SALDO", 25), ("TOTAL", 25)
            ]
            
            # Cabecera de Tabla
            pdf.set_font("Helvetica", 'B', 8)
            pdf.set_fill_color(*BLUE_COLOR)
            pdf.set_text_color(255, 255, 255)
            for label, width in cols:
                pdf.cell(width, 8, text=label, border=1, align='C', fill=True)
            pdf.ln()

            # Datos
            pdf.set_font("Helvetica", size=7)
            pdf.set_text_color(0, 0, 0)
            total_global_saldo = 0
            
            for item in data[:50]:
                op = str(item.get('op', '-'))
                fecha = str(item.get('fecha_orden', '-'))
                unn = str(item.get('unidad_negocio', '-'))[:15]
                comercio = str(item.get('cliente_nombre_comercial') or item.get('cliente_nombre', '-'))[:35]
                vendedor = str(item.get('vendedor_nombre', '-'))[:25]
                p_inicio = str(item.get('inicio_pauta', '-'))
                p_fin = str(item.get('fin_pauta', '-'))
                factura = f"{item.get('tipo_factura','') or ''} {item.get('numero_factura','') or ''}".strip() or "-"
                saldo_val = float(item.get('saldo_actual') or 0)
                total_val = float(item.get('importe_total') or 0)
                total_global_saldo += saldo_val
                
                # Fila
                pdf.cell(15, 7, text=op, border=1, align='C')
                pdf.cell(20, 7, text=fecha, border=1, align='C')
                pdf.cell(25, 7, text=unn, border=1)
                pdf.cell(55, 7, text=comercio, border=1)
                pdf.cell(35, 7, text=vendedor, border=1)
                pdf.cell(20, 7, text=p_inicio, border=1, align='C')
                pdf.cell(20, 7, text=p_fin, border=1, align='C')
                pdf.cell(35, 7, text=factura, border=1, align='C')
                
                # Saldo resaltado si es > 0
                if saldo_val > 0: pdf.set_text_color(200, 0, 0)
                pdf.cell(25, 7, text=f"${saldo_val:,.2f}", border=1, align='R')
                pdf.set_text_color(0, 0, 0)
                
                pdf.cell(25, 7, text=f"${total_val:,.2f}", border=1, align='R')
                pdf.ln()

            # Pie de tabla / Total
            pdf.ln(3)
            pdf.set_font("Helvetica", 'B', 9)
            pdf.set_x(14 + 15 + 20 + 25 + 55 + 35 + 20 + 20 + 35) # Alinear con saldo
            pdf.set_text_color(200, 0, 0)
            pdf.cell(25, 8, text=f"Total: ${total_global_saldo:,.2f}", align='R', border=1)
            
        except ImportError:
            # Fallback para fpdf antiguo si no estuviera fpdf2
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt=f"Reporte de {query_text}", ln=1, align='L')
            pdf.ln(5)
            for item in data[:40]:
                linea = f"OP: {item.get('op')} | Cliente: {item.get('cliente_nombre_comercial')} | Saldo: {item.get('saldo_actual')}"
                pdf.multi_cell(0, 8, txt=linea)
            
        pdf_out = pdf.output()
        # En fpdf2 output() devuelve bytes. En fpdf antiguo a veces string.
        if isinstance(pdf_out, (str, bytearray)):
            if isinstance(pdf_out, bytearray): pdf_out = bytes(pdf_out)
            else: pdf_out = pdf_out.encode('latin-1', 'ignore')
            
        return base64.b64encode(pdf_out).decode()
    except Exception as e: 
        safe_print(f"DEBUG: Error PDF Fatal: {e}")
        import traceback
        safe_print(traceback.format_exc())
        return f"Error creando PDF: {str(e)}"

def consultar_saldo_real(cliente: str):
    """Consulta la deuda total de un cliente en la base de datos de Supabase."""
    try:
        res = supabase.table("v_pagos_resumen").select("saldo").ilike("cliente_nombre", f"%{cliente}%").execute()
        if not res.data: return f"No se encontró al cliente '{cliente}'."
        total_deuda = sum(float(item.get("saldo") or 0) for item in res.data)
        return {"cliente": cliente, "deuda_total": total_deuda}
    except Exception as e: return f"Error en base de datos: {str(e)}"

def obtener_detalle_op(op_id: str):
    """Obtiene los detalles de una OP específica."""
    try:
        res = supabase.table("v_todas_las_op_report").select("*").ilike("op", f"%{op_id}%").execute()
        return res.data[0] if res.data else None
    except Exception: return None

def consultar_comisiones_vendedor(vendedor: str):
    """Consulta resumen de comisiones de un vendedor."""
    try:
        res = supabase.table("v_comisiones_report").select("importe_comision, esta_liquidado").eq("vendedor", vendedor).execute()
        if not res.data: return f"No encontré comisiones para {vendedor}."
        total = sum(float(i.get("importe_comision") or 0) for i in res.data)
        pendiente = sum(float(i.get("importe_comision") or 0) for i in res.data if not i.get("esta_liquidado"))
        return {"vendedor": vendedor, "total": total, "pendiente": pendiente}
    except Exception as e: return f"Error: {str(e)}"

# --- CONFIGURACIÓN DE IA (GEMINI) ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Listar modelos para debug
    try:
        print("DEBUG: Modelos disponibles:", flush=True)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}", flush=True)
    except: pass

    SYSTEM_INSTRUCTION = """
    Eres el Asistente Administrativo de JALSistemas. Ayudas a consultar saldos, pautas y cobrar deudas.
    
    REGLAS:
    1. Responde de forma concisa, profesional y con emojis de WhatsApp.
    2. Si el sistema te provee 'Contexto', úsalo para dar datos exactos.
    3. Si no tienes datos en el contexto y te preguntan por un cliente, pide el nombre completo.
    """
    
    # Ahora sí definimos las herramientas porque ya están definidas arriba
    tools = [
        consultar_saldo_real, 
        consultar_pauta_hoy, 
        obtener_detalle_op,
        buscar_datos_sistema,
        generar_reporte_excel,
        generar_reporte_pdf
    ]
    
    # Usamos Gemini 2.0 que es el que funciona con tu API Key
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-lite",
        system_instruction=SYSTEM_INSTRUCTION
    )
else:
    model = None

# --- GESTIÓN DE SESIONES Y UTILIDADES ---

# --- CONSTANTES DE ESTADOS ---
STATE_ROOT = "ROOT"
STATE_WAITING_NAME = "WAITING_NAME"
STATE_WAITING_SELECTION = "WAITING_SELECTION"
STATE_WAITING_CONFIRM = "WAITING_CONFIRM"
STATE_MENU_ACTIVE = "MENU_ACTIVE"

# --- CONSTANTES DE MENÚ ---
MENU_TIPO_CONSULTA = """
*¿Qué deseas consultar hoy?* 🤔
[1] 👤 Por Cliente
[2] 💼 Por Vendedor
"""

MENU_CLIENTE_ACTIVO = """
*OPCIONES DE CLIENTE* 👤
[1] 💰 Consultar Mi Saldo
[2] 📺 Mi Pauta de Hoy
[3] 📂 Ver Mis Órdenes (OPs)
[4] 📥 Descargar Estado de Cuenta
[0] 🔙 Cambiar Consulta / Inicio
"""

MENU_VENDEDOR_ACTIVO = """
*OPCIONES DE VENDEDOR* 💼
[1] 💵 Mis Comisiones
[2] 👥 Saldos de Mis Clientes
[3] 📈 Resumen de Ventas
[4] 📄 Descargar Reporte de Gestión
[0] 🔙 Cambiar Consulta / Inicio
"""

def obtener_sesion(numero: str):
    try:
        res = supabase.table("bot_sesiones").select("*").eq("numero_whatsapp", numero).execute()
        if res.data: return res.data[0]
        nueva = {"numero_whatsapp": numero, "estado": "IDLE", "datos_pago": {"contexto_cliente": None, "ultimo_menu": "PRINCIPAL"}}
        supabase.table("bot_sesiones").insert(nueva).execute()
        return nueva
    except: return {"estado": "IDLE", "datos_pago": {"contexto_cliente": None, "ultimo_menu": "PRINCIPAL"}}

def actualizar_sesion(numero: str, estado: str = None, datos: dict = None):
    try:
        upd = {"updated_at": "now()"}
        if estado: upd["estado"] = estado
        if datos: upd["datos_pago"] = datos
        supabase.table("bot_sesiones").update(upd).eq("numero_whatsapp", numero).execute()
    except: pass

def limpiar_sesion(numero: str):
    actualizar_sesion(numero, estado="IDLE", datos={})

async def descargar_media(message_key: dict):
    try:
        url = f"{EVO_URL}/chat/fetchMedia/{EVO_INSTANCE}"
        headers = {"apikey": EVO_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json={"key": message_key}, headers=headers)
            return res.json().get("data", {}).get("base64")
    except: return None

def send_whatsapp_message(number: str, text: str):
    try:
        url = f"{EVO_URL}/message/sendText/{EVO_INSTANCE}"
        payload = {
            "number": number,
            "text": text
        }
        headers = {"apikey": EVO_KEY, "Content-Type": "application/json"}
        
        safe_print(f"DEBUG: Intentando enviar mensaje a {url}...")
        safe_print(f"DEBUG: Enviando texto: {text[:50]}...")
        response = requests.post(url, headers=headers, json=payload)
        
        safe_print(f"DEBUG: Respuesta de Evolution: Status {response.status_code}")
        
        # Registrar en el historial (Saliente)
        log_interaction(number, text, "OUT")
        
    except Exception as e: 
        print(f"DEBUG: Error fatal en send_whatsapp_message: {e}", flush=True)

def log_interaction(numero, mensaje, direccion, nombre=None):
    try:
        supabase.table("bot_interacciones").insert({"numero": numero, "mensaje": mensaje, "direccion": direccion, "nombre_contacto": nombre}).execute()
    except: pass

# --- HANDLERS DE ESTADOS ---

def handle_root_state(sender, text, datos):
    if text == "1":
        datos["entidad_tipo"] = "CLIENTE"
        actualizar_sesion(sender, STATE_WAITING_NAME, datos)
        send_whatsapp_message(sender, "🔍 Elegiste *CLIENTES*. Por favor, escribí el nombre o razón social que buscás:")
    elif text == "2":
        datos["entidad_tipo"] = "VENDEDOR"
        actualizar_sesion(sender, STATE_WAITING_NAME, datos)
        send_whatsapp_message(sender, "🔍 Elegiste *VENDEDORES*. Por favor, escribí el nombre del vendedor:")
    else:
        send_whatsapp_message(sender, "Opción no válida.\n" + MENU_TIPO_CONSULTA)

def handle_waiting_name_state(sender, text, datos):
    try:
        tipo = datos.get("entidad_tipo", "CLIENTE")
        # Para el menú de selección, buscamos hasta 5 opciones
        results = buscar_datos_sistema(text, tipo, limite=10)
        
        if not results:
            # --- NUEVA LÓGICA: FUZZY SEARCH COMO FALLBACK ---
            safe_print(f"DEBUG: No se encontró '{text}' con ilike. Probando Fuzzy Search...")
            sugerencias_fuzzy = buscar_con_fuzzy(text, tipo)
            
            if sugerencias_fuzzy:
                msg = f"🤔 No encontré exactamente '{text}', pero ¿quisiste decir alguno de estos?\n\n"
                for idx, s in enumerate(sugerencias_fuzzy, 1):
                    msg += f"*{idx}.* {s}\n"
                msg += "\n*0.* Ninguno (Escribí otro nombre)"
                
                datos["sugerencias"] = [{"nombre": s} for s in sugerencias_fuzzy]
                actualizar_sesion(sender, estado="WAITING_SELECTION", datos=datos)
                send_whatsapp_message(sender, msg)
                return
            
            send_whatsapp_message(sender, f"❌ No encontré ningún {tipo} que coincida con '{text}'.\n\nPor favor, escribí el nombre de nuevo (probá con menos letras):")
            return

        # Eliminar duplicados por nombre
        unique_matches = []
        seen_names = set()
        for r in results:
            name = (r.get("cliente_nombre_comercial") or r.get("cliente_nombre") or r.get("vendedor_nombre") or "").strip()
            if name and name not in seen_names:
                unique_matches.append(r)
                seen_names.add(name)
        
        # Solo quedan los top 5
        unique_matches = unique_matches[:5]

        if len(unique_matches) == 1:
            # Caso ideal: 1 resultado exacto o dominante
            match = unique_matches[0]
            nombre = (match.get("cliente_nombre_comercial") or match.get("cliente_nombre") or match.get("vendedor_nombre"))
            datos["contexto_nombre"] = nombre
            actualizar_sesion(sender, estado="WAITING_CONFIRM", datos=datos)
            msg = f"🔍 Encontré: *{nombre}*\n¿Es correcto?\n\n1. ✅ Sí\n2. ❌ No, buscar otro"
            send_whatsapp_message(sender, msg)
        else:
            # Multiples coincidencias: Mostrar Menú de Sugerencias
            msg = "🤔 Encontré varias coincidencias. ¿A cuál te referís?\n\n"
            for idx, m in enumerate(unique_matches, 1):
                nombre = (m.get("cliente_nombre_comercial") or m.get("cliente_nombre") or m.get("vendedor_nombre"))
                msg += f"*{idx}.* {nombre}\n"
            
            msg += "\n*0.* Ninguno de estos (Buscar otro)"
            
            # Guardar opciones en la sesión para recuperarlas
            datos["sugerencias"] = [{"nombre": (m.get("cliente_nombre_comercial") or m.get("cliente_nombre") or m.get("vendedor_nombre"))} for m in unique_matches]
            actualizar_sesion(sender, estado="WAITING_SELECTION", datos=datos)
            send_whatsapp_message(sender, msg)
            
    except Exception as e:
        safe_print(f"DEBUG: Error en handle_waiting_name: {e}")
        send_whatsapp_message(sender, "⚠️ Hubo un error al procesar la búsqueda. Por favor intentá de nuevo.")

def handle_waiting_selection_state(sender, text, datos):
    """Maneja la elección del usuario entre múltiples sugerencias de nombres."""
    try:
        sugerencias = datos.get("sugerencias", [])
        
        if text == "0":
            datos["sugerencias"] = []
            actualizar_sesion(sender, estado="WAITING_NAME", datos=datos)
            send_whatsapp_message(sender, "Entendido. Escribí de nuevo el nombre que buscás:")
            return

        # Validar si eligió un número válido
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(sugerencias):
                seleccionado = sugerencias[idx]["nombre"]
                datos["contexto_nombre"] = seleccionado
                datos["sugerencias"] = []
                actualizar_sesion(sender, estado="WAITING_CONFIRM", datos=datos)
                msg = f"Has seleccionado: *{seleccionado}*\n¿Es correcto?\n\n1. ✅ Sí\n2. ❌ No, buscar otro"
                send_whatsapp_message(sender, msg)
                return
        
        send_whatsapp_message(sender, "Por favor, elegí un número de la lista (1 a 5) o 0 para cancelar.")
    except Exception as e:
        safe_print(f"DEBUG: Error en handle_selection: {e}")
        actualizar_sesion(sender, estado="ROOT")
        send_whatsapp_message(sender, "Error en selección. Volviendo al inicio.")

def handle_waiting_confirm_state(sender, text, datos):
    if text in ["1", "si", "sí", "confirmar"]:
        # CORRECCIÓN DE BUG: Usar contexto_nombre consistently
        nombre_confirmado = datos.get("contexto_nombre")
        if not nombre_confirmado:
            # Fallback por si acaso se perdió la variable
            nombre_confirmado = "CLIENTE DESCONOCIDO"
            
        datos["entidad_confirmada"] = nombre_confirmado
        actualizar_sesion(sender, STATE_MENU_ACTIVE, datos)
        
        menu = MENU_CLIENTE_ACTIVO if datos.get("entidad_tipo") == "CLIENTE" else MENU_VENDEDOR_ACTIVO
        send_whatsapp_message(sender, f"✅ ¡Confirmado! Estamos consultando por *{nombre_confirmado}*.\n\n" + menu)
    else:
        # Volver a pedir nombre
        actualizar_sesion(sender, STATE_WAITING_NAME, datos)
        send_whatsapp_message(sender, "Entendido. Escribí de nuevo el nombre que buscás:")

def handle_menu_active_state(sender, text, datos):
    if text in ["0", "inicio", "reset", "atras", "atrás"]:
        limpiar_sesion(sender)
        send_whatsapp_message(sender, "🔄 Volviendo al inicio...\n" + MENU_TIPO_CONSULTA)
        return

    tipo = datos.get("entidad_tipo")
    entidad = datos.get("entidad_confirmada")
    
    if tipo == "CLIENTE":
        if text == "1": # Saldo
            res = consultar_saldo_real(entidad)
            if isinstance(res, dict):
                msg = f"💰 *SALDO DE {entidad}*\nTotal adeudado: *${res['deuda_total']:,.2f}*"
                send_whatsapp_message(sender, msg + "\n\n" + MENU_CLIENTE_ACTIVO)
            else: 
                send_whatsapp_message(sender, res + "\n\n" + MENU_CLIENTE_ACTIVO)
        elif text == "2": # Pauta Hoy
            send_whatsapp_message(sender, "📅 Consultando pauta de hoy...")
            res_msg = consultar_pauta_hoy(entidad, "CLIENTE")
            send_whatsapp_message(sender, res_msg + "\n\n" + MENU_CLIENTE_ACTIVO)
        elif text == "3": # Ver OPs
            res = buscar_datos_sistema(entidad, "CLIENTE")
            if res:
                msg = f"📂 *ORDENES ACTIVAS DE {entidad}*\n"
                for r in res[:5]:
                    msg += f"• OP {r['op']}: ${r['importe_total']}\n"
                send_whatsapp_message(sender, msg + "\n" + MENU_CLIENTE_ACTIVO)
            else: send_whatsapp_message(sender, "No encontré órdenes activas.\n\n" + MENU_CLIENTE_ACTIVO)
        elif text == "4": # PDF
            send_whatsapp_message(sender, "📩 Preparando estado de cuenta en PDF... (Esto puede tardar unos segundos)")
            b64 = generar_reporte_pdf(entidad)
            if isinstance(b64, str) and len(b64) > 100:
                send_whatsapp_media(sender, b64, f"Estado_{entidad}.pdf", f"Aquí tenés el PDF de {entidad}")
            else:
                send_whatsapp_message(sender, "❌ No pude generar el PDF.")
        else:
            send_whatsapp_message(sender, "Opción no válida.\n" + MENU_CLIENTE_ACTIVO)
            
    elif tipo == "VENDEDOR":
        if text == "1": # Comisiones
            res = consultar_comisiones_vendedor(entidad)
            if isinstance(res, dict):
                msg = f"💵 *COMISIONES DE {entidad}*\n"
                msg += f"• Total histórico: *${res['total']:,.2f}*\n"
                msg += f"• Pendiente de liquidar: *${res['pendiente']:,.2f}*"
                send_whatsapp_message(sender, msg + "\n\n" + MENU_VENDEDOR_ACTIVO)
            else:
                send_whatsapp_message(sender, res + "\n\n" + MENU_VENDEDOR_ACTIVO)
        elif text == "2": # Saldos Clientes
            res = buscar_datos_sistema(entidad, "VENDEDOR")
            if res:
                total_saldo = sum(float(r.get('saldo_actual') or 0) for r in res)
                send_whatsapp_message(sender, f"👥 *CLIENTES DE {entidad}*\nSaldo total pendiente: *${total_saldo:,.2f}*\n\n" + MENU_VENDEDOR_ACTIVO)
            else: send_whatsapp_message(sender, "No encontré clientes con deuda.\n\n" + MENU_VENDEDOR_ACTIVO)
        elif text == "3": # Resumen Ventas
            send_whatsapp_message(sender, f"📈 Generando resumen de ventas para {entidad}...\n\n" + MENU_VENDEDOR_ACTIVO)
        elif text == "4": # Reporte Gestión Excel
            send_whatsapp_message(sender, "📩 Generando reporte de gestión en Excel...")
            b64 = generar_reporte_excel(entidad)
            if isinstance(b64, str) and len(b64) > 100:
                send_whatsapp_media(sender, b64, f"Reporte_{entidad}.xlsx", f"Reporte de gestión para {entidad}")
            else:
                send_whatsapp_message(sender, "❌ No pude generar el Excel.")
        else:
            send_whatsapp_message(sender, "Opción no válida.\n" + MENU_VENDEDOR_ACTIVO)

# --- WEBHOOK PRINCIPAL ---

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        event_name = data.get("event", "UNKNOWN")
        
        if event_name.lower() != "messages.upsert":
            return {"status": "ignored"}

        msg_data = data.get("data", {})
        message = msg_data.get("message", {})
        key = msg_data.get("key", {})
        if not message or key.get("fromMe"): return {"status": "ignored"}

        remote_jid = key.get("remoteJid", "")
        sender = remote_jid.split("@")[0]
        sender_clean = sender[-10:]

        # Verificar usuario habilitado
        res_u = supabase.table("perfiles").select("username, whatsapp_habilitado") \
            .ilike("numero_celular", f"%{sender_clean}%").execute()
        
        if not res_u.data or not res_u.data[0].get("whatsapp_habilitado"):
            return {"status": "unauthorized"}
        
        sesion = obtener_sesion(sender)
        estado = sesion.get("estado", STATE_ROOT)
        datos = sesion.get("datos_pago", {})

        # --- FLUJO DE IMAGEN (Comprobantes) ---
        if "imageMessage" in message:
            send_whatsapp_message(sender, "👀 Analizando comprobante de pago...")
            b64 = await descargar_media(key)
            if b64:
                # Integrar con flujo de pago si es necesario, por ahora solo aviso
                send_whatsapp_message(sender, "✅ Imagen recibida. Esta función se integrará con el menú pronto.")
            return {"status": "vision"}

        # --- FLUJO DE TEXTO ---
        text = message.get("conversation", "") or message.get("extendedTextMessage", {}).get("text", "")
        text = text.lower().strip()
        if not text: return {"status": "no_text"}

        # Registrar interacción
        log_interaction(sender, text, "IN")

        # Comandos globales
        if text in ["inicio", "reset", "hola", "buen día", "buenas"]:
            limpiar_sesion(sender)
            send_whatsapp_message(sender, "¡Hola! Soy tu Asistente Administrativo. 🤖\n" + MENU_TIPO_CONSULTA)
            return {"status": "reset"}

        # Dispatcher de Estados
        if estado == STATE_ROOT or estado == "IDLE":
            handle_root_state(sender, text, datos)
        elif estado == STATE_WAITING_NAME:
            handle_waiting_name_state(sender, text, datos)
        elif estado == STATE_WAITING_SELECTION:
            handle_waiting_selection_state(sender, text, datos)
        elif estado == STATE_WAITING_CONFIRM:
            handle_waiting_confirm_state(sender, text, datos)
        elif estado == STATE_MENU_ACTIVE:
            handle_menu_active_state(sender, text, datos)
        else:
            # Fallback a inicio si hay estado desconocido
            limpiar_sesion(sender)
            send_whatsapp_message(sender, MENU_TIPO_CONSULTA)

        return {"status": "ok"}

    except Exception as e:
        import traceback
        print(f"ERROR CRITICO WEBHOOK: {traceback.format_exc()}")
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("Super Agente WhatsApp Iniciado...")
    uvicorn.run(app, host="0.0.0.0", port=3001)
