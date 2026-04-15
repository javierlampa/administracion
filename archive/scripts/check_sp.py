import os, requests, msal
from dotenv import load_dotenv

load_dotenv()

auth_url = f"https://login.microsoftonline.com/{os.getenv('SP_TENANT_ID')}"
app = msal.ConfidentialClientApplication(os.getenv('SP_CLIENT_ID'), authority=auth_url, client_credential=os.getenv('SP_CLIENT_SECRET'))
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
headers = {'Authorization': f"Bearer {result['access_token']}"}

res_site = requests.get('https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas', headers=headers).json()
site_id = res_site['value'][0]['id']

res_list_un = requests.get(f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists?select=id,displayName', headers=headers).json()
list_un_id = next(l['id'] for l in res_list_un['value'] if l['displayName'] == 'Unidad de Negocio')

sp_units = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_un_id}/items?expand=fields&$top=1", headers=headers).json()

print(sp_units['value'][0]['fields'])
