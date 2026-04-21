import os, requests, time
from dotenv import load_dotenv
from supabase import create_client
from sharepoint_sync import get_token, get_items_incremental, parse_int, parse_num, smart_find_op_id, get_global_ops_map, smart_find_op_numero

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

def sync_pagos_total():
    print("=========================================================")
    print("  INICIANDO ESPEJADO TOTAL: TABLA PAGOS")
    print("=========================================================\n")

    db_maps = get_global_ops_map()
    
    # Vaciar tabla pagos
    print("🗑️  Vaciando tabla pagos en Supabase...")
    supabase.table("pagos").delete().neq("id", 0).execute()
    
    # Cargar de SharePoint
    print("🔄 Descargando PAGOS desde SharePoint...")
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=999"
    items = get_items_incremental(url, headers)
    
    print(f"✅ Encontrados {len(items)} registros de pagos.")
    
    pagos_data = []
    for i in items:
        f = i['fields']
        op_val = str(f.get('OP_Pagos') or '').strip()
        if not op_val: continue
        
        op_val = str(smart_find_op_numero(op_val, db_maps, is_lookup=True) or op_val).strip()

        try:
            op_id = smart_find_op_id(op_val, db_maps)
            pagos_data.append({
                'op_id':        op_id,
                'op_numero':    op_val,
                'monto_pago':   parse_num(f.get('Monto_x0020_del_x0020_Pago')),
                'fecha_pago':   f.get('Fechadelpago'),
                'tipo_pago':    f.get('TipodePago'),
                'recibo':       f.get('Recibo_x002f_Comprobante'),
                'observaciones': f.get('Observaciones'),
                'created':      f.get('Created')
            })
        except Exception as e:
            print(f"⚠️ Error parseando pago OP {op_val}: {e}")

    # Insertar en bloques
    chunk_size = 500
    count = 0
    for i in range(0, len(pagos_data), chunk_size):
        chunk = pagos_data[i:i+chunk_size]
        supabase.table("pagos").insert(chunk).execute()
        count += len(chunk)
        print(f"  -> Insertados {count} de {len(pagos_data)}...")

    print(f"\n✅ ESPEJADO DE PAGOS FINALIZADO: {count} registros subidos.")

if __name__ == "__main__":
    sync_pagos_total()
