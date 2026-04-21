import os
from dotenv import load_dotenv
from sharepoint_sync import get_global_ops_map, smart_find_op_id

load_dotenv()

db_maps = get_global_ops_map()
op_to_id, _ = db_maps

target = "4098"
found_id = smart_find_op_id(target, db_maps)
print(f"Buscando '{target}': ID encontrado = {found_id}")

target2 = "4098-07"
found_id2 = smart_find_op_id(target2, db_maps)
print(f"Buscando '{target2}': ID encontrado = {found_id2}")

# Ver si estan en el mapa directamente
print(f"¿'4098' está en map_str?: {target in op_to_id}")
print(f"¿'4098-07' está en map_str?: {target2 in op_to_id}")
