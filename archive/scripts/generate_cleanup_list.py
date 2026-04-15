import csv
import os

CSV_DIR = r"f:\JAVIER PRIVADO\APP PHYTON\ADMINISTRACION\csv"
REPORT_FILE = r"f:\JAVIER PRIVADO\APP PHYTON\ADMINISTRACION\DOCS\LISTA_BORRADO_SHAREPOINT.md"

def get_orphans(csv_name, op_col):
    csv_path = os.path.join(CSV_DIR, csv_name)
    ids = []
    if not os.path.exists(csv_path):
        return []
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            op = row.get(op_col)
            # Definimos huérfano como OP vacío o con texto de error común
            if not op or str(op).strip() == "" or "S/N" in str(op).upper():
                ids.append(row.get("ID") or row.get("\ufeffID") or "N/A")
    return ids

# Análisis
pagos_orphans = get_orphans("Pagos.csv", "OP")
tv_orphans = get_orphans("TV.csv", "OP_TP")
un_orphans = get_orphans("Unidad de Negocio.csv", "OP_UNN")

with open(REPORT_FILE, "w", encoding="utf-8") as r:
    r.write("# 📋 Lista de Registros Huérfanos para Limpieza en SharePoint\n\n")
    r.write("Estos registros no tienen una OP válida asociada y fueron ignorados en la sincronización. Se recomienda borrarlos de SharePoint para mantener la integridad.\n\n")
    
    r.write(f"### 1. Lista 'Pagos' ({len(pagos_orphans)} registros)\n")
    r.write("> **IDs a borrar:** " + ", ".join(pagos_orphans) + "\n\n")
    
    r.write(f"### 2. Lista 'TV' ({len(tv_orphans)} registros)\n")
    r.write("> **IDs a borrar:** " + ", ".join(tv_orphans) + "\n\n")
    
    r.write(f"### 3. Lista 'Unidad de Negocio' ({len(un_orphans)} registros)\n")
    r.write("> **IDs a borrar:** " + ", ".join(un_orphans) + "\n\n")

print("Reporte de limpieza generado con éxito.")
