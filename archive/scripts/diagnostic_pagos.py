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

# Traemos todas las OPs de nuestra DB para cruzar
res_ops = supabase.table('ordenes_publicidad').select('id, op').execute()
ops_by_text = {str(r['op']).strip(): r['id'] for r in res_ops.data}
ops_by_id = {r['id']: r['op'] for r in res_ops.data}

print(f"{'ID Pago':<10} | {'Campo OP':<15} | {'LookupID':<10} | {'¿Existe en DB?':<15} | {'OP en DB'}")
print("-" * 70)

count = 0
for item in items.get('value', []):
    f = item['fields']
    pago_id = f.get('id')
    op_text = str(f.get('OP') or '').strip()
    op_lookup_id = f.get('OPLookupId')
    
    # Intento 1: Por texto (lo que fallaba)
    match_text = ops_by_text.get(op_text)
    # Intento 2: Por ID numérico (lo que hay que arreglar)
    match_id = ops_by_id.get(op_lookup_id)
    
    if match_text is None and count < 10:
        existe = "SÍ (por ID)" if match_id else "NO"
        op_en_db = match_id if match_id else "N/A"
        print(f"{pago_id:<10} | {repr(op_text):<15} | {str(op_lookup_id):<10} | {existe:<15} | {op_en_db}")
        count += 1

print("-" * 70)
