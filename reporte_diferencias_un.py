import os
from dotenv import load_dotenv
from supabase import create_client

# Script AUDITORÍA 2026 (Nombres Corregidos)
load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def get_report():
    print("🚀 Iniciando auditoría 2026 corregida...")
    
    # 1. Traer TODAS las Órdenes de 2026
    all_ops = []
    for i in range(0, 10000, 1000):
        res = supabase.table('ordenes_publicidad').select('op, importe_total, id').filter('fecha_orden', 'gte', '2026-01-01').filter('importe_total', 'gt', 0).range(i, i + 999).execute()
        if not res.data: break
        all_ops.extend(res.data)
    
    # 2. Traer sumas de UN
    all_un = []
    for i in range(0, 10000, 1000):
        res = supabase.table('unidades_negocio').select('op_id, importe_total').range(i, i + 999).execute()
        if not res.data: break
        all_un.extend(res.data)
            
    un_sums = {}
    for r in all_un:
        oid = r['op_id']
        if oid:
            un_sums[oid] = un_sums.get(oid, 0) + float(r['importe_total'] or 0)
            
    print(f"📊 Analizando {len(all_ops)} órdenes...")
    differences = []
    total_maestra = 0
    total_unidades = 0
    
    for op in all_ops:
        oid = op['id']
        m_total = float(op['importe_total'] or 0)
        u_total = un_sums.get(oid, 0)
        
        total_maestra += m_total
        total_unidades += u_total
        
        diff = round(m_total - u_total, 2)
        if abs(diff) > 1:
            differences.append({'op': op['op'], 'm': m_total, 'u': u_total, 'd': diff})
            
    print(f"\n💰 SUMA MAESTRA 2026: ${total_maestra:,.2f}")
    print(f"💰 SUMA UNIDADES 2026: ${total_unidades:,.2f}")
    print(f"⚖️ DIFERENCIA TOTAL: ${total_maestra - total_unidades:,.2f}")

    if not differences:
        print("\n✅ ¡PARIDAD TOTAL ALCANZADA! Todo coincide perfectamente.")
    else:
        print(f"\n❌ Faltan {len(differences)} diferencias:")
        for d in differences[:10]:
            print(f"   - OP {d['op']} | Maestra: ${d['m']:,.2f} | UN: ${d['u']:,.2f} | Diff: ${d['d']:,.2f}")

if __name__ == "__main__":
    get_report()
