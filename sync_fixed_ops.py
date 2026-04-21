import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import requests
import msal

load_dotenv()

def sync_specific_ops():
    # Lista de OPs a reparar (las que tenían nombre NULL)
    ops_to_fix = [
        "36827/12", "5646-", "2026-00963", "6090-05", "37416",
        "01142", "7663", "35454", "30480/0", "5418-04",
        "377330", "123147", "5672-05", "36834", "6130", "5666-3", "5588"
    ]
    
    # 1. Auth SharePoint
    app = msal.ConfidentialClientApplication(
        os.getenv('SP_CLIENT_ID'),
        authority=f"https://login.microsoftonline.com/{os.getenv('SP_TENANT_ID')}",
        client_credential=os.getenv('SP_CLIENT_SECRET')
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Auth Supabase
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    # Get Site ID
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    print(f"🚀 Iniciando reparación de {len(ops_to_fix)} OPs específicas...")
    
    counts = 0
    for op in ops_to_fix:
        # Buscamos en SharePoint todas las unidades de negocio para esta OP_UNN
        # Nota: OP_UNN puede ser el numero de OP real
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$filter=fields/OP_UNN eq '{op}'"
        res = requests.get(url, headers=headers).json()
        
        items = res.get('value', [])
        for item in items:
            fields = item['fields']
            unit_name = fields.get('Unidaddenegocio0')
            importe = float(fields.get('ImporteTotal') or 0)
            
            if unit_name:
                # Actualizamos en Supabase
                # Buscamos por op_numero y unidad_negocio que sea null (o por el nombre que tenga ahora)
                supabase.table('unidades_negocio').update({
                    'unidad_negocio': unit_name
                }).eq('op_numero', op).is_('unidad_negocio', 'null').execute()
                
                print(f"✅ OP {op}: Asignada a '{unit_name}' (${importe:,.2f})")
                counts += 1

    print(f"\n🏆 ¡REPARACIÓN FINALIZADA! Se actualizaron {counts} registros.")

if __name__ == "__main__":
    sync_specific_ops()
