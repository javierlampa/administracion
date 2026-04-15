import os
import requests
from dotenv import load_dotenv
import msal

load_dotenv('.env')

TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def get_items(url, headers):
    resp = requests.get(url, headers=headers).json()
    return resp

def run():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']

    # Get Site lists to see the names
    lists = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists", headers=headers).json()
    print("=== SP LISTS ===")
    for ls in lists.get('value', []):
        print(f"Name: {ls['name']} | Display: {ls['displayName']}")

run()
