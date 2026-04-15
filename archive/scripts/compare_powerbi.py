import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

powerbi_totals = {
    "A LA CARTA": 3464500.00,
    "ADN": 414937.50,
    "Agro y Negocios": 2184860.00,
    "ALMA FLAMENCA": 500000.00,
    "AM1020-ROTATIVO DIARIO": 2488300.00,
    "AMANECIDOS": 1842000.00,
    "BN BD": 1885087.50,
    "BONUS SHOW": 2000000.00,
    "Buena Gente": 525000.00,
    "Cobertura Municipal AM 1020": 5475500.00,
    "Cobertura Municipal Telesol": 19309075.00,
    "COBERTURA MUNICIPAL ZONDA": 3772000.00,
    "CON TIZA Y PIZARRON": 595000.00,
    "Construyendo a mamá": 993149.50,
    "Desenfocados": 600000.00,
    "DIARIO TELESOL": 4761000.00,
    "DIARIO ZONDA": 3852117.00,
    "DQE": 1887600.00,
    "EL DIA PERFECTO": 437500.00,
    "EMPRESARIAL": 2000000.00, # Wait, image says 200.000,00. Fixed to 200000
    "Especial": 363000.00,
    "HISTORIA": 1115000.00,
    "INSOPORTABLES": 3150000.00,
    "LA MINERIA Y LA GENTE": 643149.50,
    "LA NOCHE DE TELESOL": 991200.00,
    "La Tarde es Nuestra": 20000.00,
    "La Ventana": 14082950.00,
    "MAS CICLISMO": 1500000.00,
    "MINEROS": 643149.50,
    "MODO TARDE": 3120000.00,
    "MOTORES EN MARCHA": 750000.00,
    "NO TAN SERIOS": 640000.00,
    "NOTICIEROS, 2": 27113200.24,
    "NOTICIEROS, LOS 3": 13955873.82,
    "Platea Nacional": 800000.00,
    "PREGUNTADOS SAN JUAN": 1312000.00,
    "PRODUCIENDO": 130000.00, # Missed this one earlier, just saw it in image!
    "REDES": 70000.00,
    "ROTATIVO AM 1020": 7541353.00,
    "ROTATIVO TELESOL": 42683193.58,
    "ROTATIVO ZONDA": 2456000.00,
    "San Juan Construye": 1343149.50,
    "SIEMPRE CON VOS": 1512500.00,
    "TLN": 19173691.12,
    "TRANSMISION": 1625000.00,
    "Zonda Noticias": 4060000.00,
    "(En blanco)": 3150680.00 # First row in image 1
}

# Fix Empresarial:
powerbi_totals['EMPRESARIAL'] = 200000.00

res = supabase.rpc('get_evolucion_programa_metrics', {
    'p_start_date': '2026-01-01',
    'p_end_date': '2026-04-14',
    'p_empresa': 'Todas'
}).execute()

data = res.data or {}
matrix = data.get('matrixImporte', [])

nextjs_totals = {}
for row in matrix:
    prog = row.get('un')
    tot = row.get('total', 0)
    nextjs_totals[prog] = nextjs_totals.get(prog, 0) + tot

all_progs = set(powerbi_totals.keys()).union(set(nextjs_totals.keys()))

print(f"{'PROGRAMA':<35} | {'POWERBI':<15} | {'NEXTJS':<15} | {'DIFF (Nx - PBI)':<15}")
print("-" * 88)

for p in sorted(all_progs):
    pbi = powerbi_totals.get(p, 0)
    # Next.js might have 'PROGRAMA' capitalized differently, but actually it returns exactly DB string
    nxt = nextjs_totals.get(p, 0)
    diff = nxt - pbi
    if abs(diff) > 1:
        print(f"{p:<35} | {pbi:<15,.2f} | {nxt:<15,.2f} | {diff:<15,.2f}")

print("-" * 88)
print(f"TOTAL POWERBI: {sum(powerbi_totals.values()):,.2f}")
print(f"TOTAL NEXT.JS: {sum(nextjs_totals.values()):,.2f}")
