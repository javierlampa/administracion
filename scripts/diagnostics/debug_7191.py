import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_op():
    tenant_id = os.getenv("SP_TENANT_ID")
    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    
    # Token
    url_token = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    token = requests.post(url_token, data=data).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Site ID
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=SistemadeVentas2", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Buscar OP 7191 en la lista
    # Como el filtro de Graph a veces es mañoso, vamos a bajar todo y buscar en Python para estar 100% seguros
    url_ops = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields"
    print("Buscando OP 7191 en SharePoint...")
    
    all_items = []
    next_url = url_ops
    while next_url:
        res = requests.get(next_url, headers=headers).json()
        items = res.get('value', [])
        for i in items:
            f = i['fields']
            op_val = str(f.get('OP')).strip() if f.get('OP') else ""
            if op_val == "7191":
                print(f"✅ ENCONTRADA! ID SP: {f.get('id')} | Titulo: {f.get('Title')} | Fecha: {f.get('Fecha_x0020_de_x0020_la_x0020_Or')}")
        next_url = res.get('@odata.nextLink')

if __name__ == "__main__":
    debug_op()
