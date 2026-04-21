import os, requests
from dotenv import load_dotenv

load_dotenv()
tenant_id = os.getenv("SP_TENANT_ID")
client_id = os.getenv("SP_CLIENT_ID")
secret = os.getenv("SP_CLIENT_SECRET")

import msal
app = msal.ConfidentialClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant_id}", client_credential=secret)
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
token = result["access_token"]
headers = {'Authorization': f'Bearer {token}'}

site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
site_id = site['value'][0]['id']

url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=999"
all_items = []
current_url = url
while current_url:
    resp = requests.get(current_url, headers=headers).json()
    if 'value' in resp: all_items.extend(resp['value'])
    current_url = resp.get('@odata.nextLink')

print(f"Total pagos fetched: {len(all_items)}")

target_op_ids = [228] # just an example

for i in all_items:
    f = i['fields']
    op_val = str(f.get('OP') or '').strip()
    op_lookup = f.get('OPLookupId')
    
    # We want to find payments for 102/0 and 1330
    if ('102/0' in f.values() or '1330' in f.values() or op_val == '102/0' or op_val == '1330'):
        print(f"FOUND 102/0 directly in fields! -> {f}")
    
    if str(f.get('OP')).strip() in ["102/0", "1330"]:
        print(f"MATCH OP: {f}")
