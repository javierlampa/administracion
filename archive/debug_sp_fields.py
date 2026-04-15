import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def debug_list(list_name):
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']

    print(f"\n🔍 Analizando Lista: {list_name}...")
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items?expand=fields&$top=1"
    res = requests.get(url, headers=headers).json()
    
    if 'value' in res and len(res['value']) > 0:
        fields = res['value'][0]['fields']
        for k, v in fields.items():
            print(f"  -> {k}: {v}")
    else:
        print("❌ No se encontraron registros o error de lista.")

if __name__ == "__main__":
    debug_list("TV")
