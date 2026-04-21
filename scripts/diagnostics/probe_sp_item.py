import os, requests
from dotenv import load_dotenv
from sharepoint_sync import get_token

load_dotenv()
SITE_NAME_SEARCH = os.getenv("SP_SITE_NAME", "Sistema de Ventas")

def probe_7256():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Buscamos el item 7256 directamente
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items/7256?expand=fields"
    
    resp = requests.get(url, headers=headers).json()
    if 'fields' in resp:
        f = resp['fields']
        print(f"\n--- DATOS REALES DE SHAREPOINT PARA ID 7256 ---")
        for k, v in f.items():
            print(f"  {k}: {v}")
    else:
        print(f"No se encontró el item 7256 en SharePoint. Respuesta: {resp}")

if __name__ == "__main__":
    probe_7256()
