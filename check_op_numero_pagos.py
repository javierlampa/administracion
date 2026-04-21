"""
Diagnóstico: busca el pago del recibo 13417 (OP 102/2026) y muestra
todos los pagos que tienen op_numero como número puro (ID de SharePoint)
en lugar de texto de OP.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

print("=== Buscando recibo 13417 ===")
res = supabase.table("pagos").select("id,op_numero,importe_pago,recibo_numero,fecha_pago").eq("recibo_numero", "13417").execute()
print(f"  Encontrados: {len(res.data)} resultados")
for r in res.data:
    print(f"  op_numero='{r['op_numero']}' | importe={r['importe_pago']} | fecha={r['fecha_pago']}")

print("\n=== Muestra de 20 op_numero en pagos (para ver formato) ===")
res2 = supabase.table("pagos").select("op_numero").limit(20).execute()
for r in res2.data:
    print(f"  '{r['op_numero']}'")

print("\n=== Pagos con op_numero que parecen IDs numéricos (sin / ni letras) ===")
# Trae todos y filtra en Python
all_pagos = []
offset = 0
while True:
    res3 = supabase.table("pagos").select("id,op_numero,importe_pago").range(offset, offset+999).execute()
    if not res3.data: break
    all_pagos.extend(res3.data)
    if len(res3.data) < 1000: break
    offset += 1000

numericos = [p for p in all_pagos if p['op_numero'] and p['op_numero'].strip().isdigit()]
texto = [p for p in all_pagos if p['op_numero'] and not p['op_numero'].strip().isdigit()]
sin = [p for p in all_pagos if not p['op_numero']]

total_num = sum(p['importe_pago'] or 0 for p in numericos)
total_txt = sum(p['importe_pago'] or 0 for p in texto)
total_sin = sum(p['importe_pago'] or 0 for p in sin)

print(f"\n  TOTAL pagos en tabla           : {len(all_pagos)}")
print(f"  Con op_numero NUMÉRICO (SP ID) : {len(numericos)} → ${total_num:,.2f}  ← ESTOS NO SE VINCULAN")
print(f"  Con op_numero TEXT (correcto)  : {len(texto)} → ${total_txt:,.2f}")
print(f"  Sin op_numero                  : {len(sin)} → ${total_sin:,.2f}")

if numericos:
    print("\n  Primeros 5 numéricos:")
    for p in numericos[:5]:
        print(f"    op_numero='{p['op_numero']}' | importe={p['importe_pago']}")
