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

# Search for payments of ANDINA
url_search = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=50"
items = requests.get(url_search, headers=headers).json()["value"]

andina_payments = []
for i in items:
    f = i["fields"]
    cliente = str(f.get("Cliente", ""))
    if "ANDINA" in cliente.upper():
        andina_payments.append(f)

print(f"Total payments found in SP (top 50 check): {len(items)}")
print(f"Andina payments in that batch: {len(andina_payments)}")
for p in andina_payments:
    print(f"ID: {p['id']} | OP: {p.get('OP')} | OPLookupId: {p.get('OPLookupId')} | Cliente: {p.get('Cliente')} | Importe: {p.get('ImportePago')}")
