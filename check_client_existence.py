import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

def find_missing_client():
    tenant_id = os.getenv("SP_TENANT_ID")
    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    
    auth_url = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=auth_url, client_credential=client_secret)
    token_res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    token = token_res['access_token']
    
    headers = {'Authorization': f'Bearer {token}'}
    site_res = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
    site_id = site_res['value'][0]['id']
    
    # Probar IDs 3624 y 3626
    for cid in [3624, 3626]:
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Clientes_1/items/{cid}?expand=fields"
        res = requests.get(url, headers=headers).json()
        if 'error' in res:
            print(f"FAILED: ID {cid} - {res['error']['message']}")
        else:
            print(f"SUCCESS: ID {cid} - {res['fields'].get('Title')}")

if __name__ == "__main__":
    find_missing_client()
