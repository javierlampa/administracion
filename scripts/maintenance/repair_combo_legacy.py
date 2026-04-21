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

def repair():
    print("🚀 Iniciando reparación de Ventas Combo...")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Obtener ID del sitio
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # El nombre que vimos en la inspección fue VentaCOMBO, pero si ese da False,
    # es probable que el que tiene el dato sea 'Venta_x0020_COMBO' (con espacio)
    # Graph API a veces es ambiguo. Probaremos traer TODAS las órdenes del 2023 y filtrar en Python.
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=999"
    
    all_items = []
    current_url = url
    while current_url:
        resp = requests.get(current_url, headers=headers)
        res = resp.json()
        if 'value' in res: all_items.extend(res['value'])
        current_url = res.get('@odata.nextLink')

    print(f"🔎 Se encontraron {len(all_items)} órdenes marcadas como COMBO en SharePoint.")
    
    fixed = 0
    for i in all_items:
        f = i['fields']
        item_id = f.get('id')
        item_op = str(f.get('OP')).strip()
        
        # Estrategia agresiva: cualquier campo que contenga 'combo' y sea True/1
        is_combo = False
        for k, v in f.items():
            if 'combo' in k.lower() and (v == True or v == 1 or str(v).lower() == 'true'):
                is_combo = True
                break
        
        if is_combo:
            # Actualizamos en Supabase
            try:
                supabase.table("ordenes_publicidad").update({"venta_combo": True}).eq("id", item_id).execute()
                print(f"✅ OP {item_op} (ID {item_id}) marcada como COMBO.")
                fixed += 1
            except Exception as e:
                print(f"❌ Error en OP {item_op}: {e}")

    print(f"\n🏆 Finalizado. Se actualizaron {fixed} órdenes.")

if __name__ == "__main__":
    repair()
