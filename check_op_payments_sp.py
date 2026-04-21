import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

# Config
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get Site ID
res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
site_id = res_site["value"][0]["id"]

# Search for payments of OP ID 7287 (6927-04)
# SharePoint filter syntax for numeric fields
url_search = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$filter=fields/OPLookupId eq 7287"
res = requests.get(url_search, headers=headers).json()

print(f"Payments found for OP ID 7287: {len(res.get('value', []))}")
for i in res.get('value', []):
    f = i['fields']
    print(f"ID: {f['id']} | Importe: {f.get('ImportePago')} | Saldo: {f.get('Saldo')}")
