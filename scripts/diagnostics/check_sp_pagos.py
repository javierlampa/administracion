import os, requests
from sharepoint_sync import get_token, get_items_incremental
from dotenv import load_dotenv

load_dotenv()
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=1"
res = get_items_incremental(url, headers)
if res:
    print(res[0]['fields'].keys())
    print("\nSAMPLE ITEM:")
    print(res[0]['fields'])
else:
    print("No items found.")
