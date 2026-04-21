import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SITE_ID = os.getenv("SITE_ID")

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def debug_op(op_numero):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscamos en la lista Pagos
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/Pagos/items?expand=fields"
    # SharePoint doesn't allow complex filtering on non-indexed text columns easily via Graph items 
    # but we can try ilike/eq if it's indexed or just pull top 2000 and find it.
    
    print(f"Buscando OP {op_numero} en SharePoint...")
    current_url = url
    found = False
    while current_url:
        resp = requests.get(current_url, headers=headers).json()
        items = resp.get('value', [])
        for item in items:
            f = item.get('fields', {})
            # Buscamos en Title o OP o Pago_x0020_de_x0020_OP
            title = str(f.get('Title', ''))
            op_field = str(f.get('Pago_x0020_de_x0020_OP', ''))
            
            if op_numero in title or op_numero in op_field:
                print(f"ENCONTRADO en SP: ID={item['id']}, Title={title}, OP_Field={op_field}")
                print(f"Campos: {f}")
                found = True
                
        current_url = resp.get('@odata.nextLink')
        if not current_url: break

    if not found:
        print("NO se encontró la OP en los ítems de SharePoint.")

if __name__ == "__main__":
    debug_op("6499-02-26")
