import os, requests, msal
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
tenant_id = os.getenv('SP_TENANT_ID')
client_id = os.getenv('SP_CLIENT_ID')
client_secret = os.getenv('SP_CLIENT_SECRET')

auth_url = f'https://login.microsoftonline.com/{tenant_id}'
app = msal.ConfidentialClientApplication(client_id, authority=auth_url, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
token = result['access_token']
headers = {'Authorization': f'Bearer {token}'}

site_id = requests.get('https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas', headers=headers).json()['value'][0]['id']
items = requests.get(f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=5000', headers=headers).json()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
ops = {r['op'] for r in supabase.table('ordenes_publicidad').select('op').execute().data}

count = 0
for item in items.get('value', []):
    f = item['fields']
    op_val = str(f.get('OP') or '').strip()
    op_lookup = str(f.get('OPLookupId') or '').strip()
    if op_val not in ops and count < 10:
        print(f"ID={f.get('id')} | OP={repr(op_val)} | OPLookupId={op_lookup} | Importe={f.get('ImportePago')} | Fecha={f.get('FechadePago')}")
        count += 1

print('--- Fin de muestra ---')
