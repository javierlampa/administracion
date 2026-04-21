import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

def list_all_sp_lists():
    TENANT_ID = os.getenv("SP_TENANT_ID")
    CLIENT_ID = os.getenv("SP_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
    
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    res_lists = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists", headers=headers).json()
    
    print("--- LISTAS DISPONIBLES EN SHAREPOINT ---")
    for l in res_lists.get('value', []):
        print(f"- {l['displayName']} (Nombre Interno: {l['name']})")

if __name__ == "__main__":
    list_all_sp_lists()
