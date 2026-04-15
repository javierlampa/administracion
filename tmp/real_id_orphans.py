import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

# Config
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def get_all_items(url, headers):
    all_items = []
    while url:
        resp = requests.get(url, headers=headers)
        res = resp.json()
        if 'value' in res: all_items.extend(res['value'])
        url = res.get('@odata.nextLink')
    return all_items

def identify_invalid_refs():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # 1. Obtener todas las OPs válidas de "Orden de Publicidad"
    print("Cargando OPs maestras...")
    ordenes_raw = get_all_items(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=5000", headers)
    valid_ops = set()
    for i in ordenes_raw:
        op = i['fields'].get('OP')
        if op: valid_ops.add(str(op).strip())
    
    print(f"Total de OPs maestras válidas: {len(valid_ops)}")

    lists = [
        ("Pagos", "OP"),
        ("TV", "OP_TP"),
        ("Unidad de Negocio", "OP_UNN")
    ]
    
    report = "# 📋 Lista de Registros con OP INEXISTENTE en Maestros\n\n"
    report += "Estos registros tienen una OP que no figura en la lista de 'Orden de Publicidad'. Bórralos para sanear la base.\n\n"
    
    for sp_name, op_field in lists:
        print(f"Cruzando {sp_name}...")
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_name}/items?expand=fields&$top=5000"
        items = get_all_items(url, headers)
        
        invalid_ids = []
        for i in items:
            f = i['fields']
            op = str(f.get(op_field) or "").strip()
            
            # Si tiene OP pero NO está en la lista maestra
            if op and op not in valid_ops:
                invalid_ids.append(f"{i['id']} (OP: {op})")
            elif not op:
                # También incluimos los vacíos por si acaso
                invalid_ids.append(f"{i['id']} (VACÍO)")
        
        report += f"### {sp_name} ({len(invalid_ids)} registros inválidos)\n"
        report += "> **IDs a borrar:** " + ", ".join(invalid_ids) + "\n\n"
        
    with open(r"f:\JAVIER PRIVADO\APP PHYTON\ADMINISTRACION\DOCS\LISTA_BORRADO_SHAREPOINT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Reporte de limpieza por cruce actualizado.")

if __name__ == "__main__":
    identify_invalid_refs()
