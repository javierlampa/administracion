import os
import requests
import msal
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def surgical_sync():
    # 1. Clientes que sabemos que faltan (según el reporte de errores)
    missing_client_ids = [3624, 3626]
    # 2. OPs que sabemos que fallaron
    failed_ops = ["1732", "1728", "1728-03", "1728-04"]
    
    # Auth
    app = msal.ConfidentialClientApplication(
        os.getenv('SP_CLIENT_ID'),
        authority=f"https://login.microsoftonline.com/{os.getenv('SP_TENANT_ID')}",
        client_credential=os.getenv('SP_CLIENT_SECRET')
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
    headers = {'Authorization': f'Bearer {token}'}
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    print("🩹 Iniciando Sincronización Quirúrgica...")
    
    # Sincronizar Clientes faltantes
    for cid in missing_client_ids:
        print(f"  -> Recuperando Cliente ID {cid}...")
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Clientes/items/{cid}?expand=fields"
        res = requests.get(url, headers=headers).json()
        if 'fields' in res:
            f = res['fields']
            supabase.table('clientes').upsert({
                'id': f.get('id'),
                'nombre_cliente': f.get('Title'),
                'modified': f.get('Modified')
            }).execute()
            print(f"     ✅ Cliente '{f.get('Title')}' recuperado.")

    # Sincronizar Órdenes faltantes (por ID de SharePoint si es posible)
    # Según el log: OP 1732 es SP_ID 7571, OP 1728 es SP_ID 7579, etc.
    failed_sp_ids = [7571, 7579, 7580, 7581]
    
    for spid in failed_sp_ids:
        print(f"  -> Recuperando Orden SP_ID {spid}...")
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items/{spid}?expand=fields"
        res = requests.get(url, headers=headers).json()
        if 'fields' in res:
            f = res['fields']
            # Mapeo básico necesario
            supabase.table('ordenes_publicidad').upsert({
                'id': f.get('id'),
                'op': str(f.get('OP')).strip(),
                'empresa': f.get('Empresa'),
                'cliente_id': f.get('ClientesLookupId'),
                'vendedor_id': f.get('VendedorLookupId'),
                'fecha_orden': f.get('Fecha_x0020_de_x0020_la_x0020_Ord'),
                'importe_bruto': float(f.get('Importe_x0020_Bruto_x0020_S_x002f_-') or 0),
                'venta_combo': f.get('Venta_x0020_COMBO') == True
            }).execute()
            print(f"     ✅ Orden OP {f.get('OP')} recuperada.")

    # Finalmente, relanzamos la sincronización de UNIDADES DE NEGOCIO para estas órdenes
    print("  -> Refrescando Unidades de Negocio para estas órdenes...")
    for spid in failed_sp_ids:
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$filter=fields/OP_UNNLookupId eq {spid}"
        res = requests.get(url, headers=headers).json()
        for item in res.get('value', []):
            f = item['fields']
            # Necesitamos el op_numero real
            res_op = supabase.table('ordenes_publicidad').select('op').eq('id', spid).single().execute()
            op_num = res_op.data['op'] if res_op.data else str(spid)
            
            supabase.table('unidades_negocio').upsert({
                'op_id': spid,
                'op_numero': op_num,
                'unidad_negocio': f.get('Unidaddenegocio0'),
                'importe_total': float(f.get('ImporteTotal') or 0)
            }).execute()
            print(f"     ✅ Unidad '{f.get('Unidaddenegocio0')}' para OP {op_num} recuperada.")

    print("\n🏆 ¡OPERACIÓN QUIRÚRGICA FINALIZADA!")

if __name__ == "__main__":
    surgical_sync()
