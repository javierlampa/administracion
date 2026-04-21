import os
import requests
import msal
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Config
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

supabase = create_client(URL, KEY)

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def repair_all_versions():
    print("🚀 Iniciando reparación MASIVA de Ventas Combo (revisando duplicados)...")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Traemos TODOS los items de la lista (paginado)
    all_items = []
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=999"
    current_url = url
    while current_url:
        resp = requests.get(current_url, headers=headers)
        res = resp.json()
        if 'value' in res: all_items.extend(res['value'])
        current_url = res.get('@odata.nextLink')

    print(f"📦 Procesando {len(all_items)} registros de SharePoint...")
    
    fixed = 0
    for i in all_items:
        f = i['fields']
        # Usamos el ID interno de SharePoint para actualizar, que es único universal
        sp_internal_id = f.get('id')
        item_op = str(f.get('OP')).strip()
        
        is_combo = any('combo' in k.lower() and (v == True or v == 1 or str(v).lower() == 'true') for k, v in f.items())
        
        if is_combo:
            try:
                # Actualizamos en Supabase usando el ID (que coincide con el ID de SharePoint)
                supabase.table("ordenes_publicidad").update({"venta_combo": True}).eq("id", sp_internal_id).execute()
                print(f"✅ OP {item_op} (ID SP: {sp_internal_id}) marcada como COMBO.")
                fixed += 1
            except Exception as e:
                pass # Probablemente la OP no está en Supabase todavía

    print(f"\n🏆 Finalizado. Se actualizaron {fixed} órdenes como COMBO.")

if __name__ == "__main__":
    repair_all_versions()
