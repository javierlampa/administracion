import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

def inspect():
    TENANT_ID = os.getenv("SP_TENANT_ID")
    CLIENT_ID = os.getenv("SP_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
    
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Buscamos la OP 1201 que sabemos que es COMBO en tu captura
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$filter=fields/OP eq '1201'"
    resp = requests.get(url, headers=headers).json()
    
    if 'value' in resp and len(resp['value']) > 0:
        fields = resp['value'][0]['fields']
        print("--- CAMPOS ENCONTRADOS ---")
        for k, v in fields.items():
            if 'combo' in k.lower() or 'venta' in k.lower():
                print(f"DEBUG: {k} -> {v}")
        print("\nLista completa de campos para referencia:")
        print(list(fields.keys()))
    else:
        print("No se encontró la OP 1201 para inspección.")

if __name__ == "__main__":
    inspect()
