import os, requests, msal
from dotenv import load_dotenv

load_dotenv()
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_ID = os.getenv("SITE_ID")

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        print(f"Error obteniendo token: {result.get('error_description')}")
        return None
    return result["access_token"]

def debug_fields(op_numero):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/Pagos/items?expand=fields&$top=999"
    
    current_url = url
    while current_url:
        resp = requests.get(current_url, headers=headers).json()
        items = resp.get('value', [])
        for i in items:
            f = i['fields']
            vals = [str(f.get(k, '')).strip() for k in ['Title', 'Pago_x0020_de_x0020_OP', 'OP']]
            if op_numero in vals:
                print(f"\n--- CAMPOS ENCONTRADOS PARA {op_numero} (Item ID: {i['id']}) ---")
                for k, v in f.items():
                    print(f"  {k}: {v}")
                return
        current_url = resp.get('@odata.nextLink')

if __name__ == "__main__":
    debug_fields("7191")
