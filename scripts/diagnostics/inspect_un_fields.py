import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

def inspect_un_fields():
    TENANT_ID = os.getenv("SP_TENANT_ID")
    CLIENT_ID = os.getenv("SP_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
    
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Inspeccionar items de Unidad de Negocio
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$top=5"
    resp = requests.get(url, headers=headers).json()
    
    if 'value' in resp and len(resp['value']) > 0:
        fields = resp['value'][0]['fields']
        print("--- CAMPOS EN LISTA UNIDADES DE NEGOCIO ---")
        for k, v in fields.items():
            if 'unidad' in k.lower() or 'negocio' in k.lower() or 'op' in k.lower():
                print(f"{k}: {v}")
    else:
        print("No se encontraron items en Unidad de Negocio.")

if __name__ == "__main__":
    inspect_un_fields()
