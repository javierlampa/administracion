from sharepoint_sync import get_token
import requests, os
from dotenv import load_dotenv

load_dotenv()
t=get_token()
h={'Authorization': f'Bearer {t}'}
r_s=requests.get(f"https://graph.microsoft.com/v1.0/sites?search={os.getenv('SP_SITE_NAME', 'Sistema de Ventas')}", headers=h).json()
s_id=r_s['value'][0]['id']
r_i=requests.get(f"https://graph.microsoft.com/v1.0/sites/{s_id}/lists/Pagos/items?expand=fields&$top=1", headers=h).json()
f = r_i['value'][0]['fields']
print("Campos disponibles en Pagos:")
for k in sorted(f.keys()):
    print(f"  {k}")
