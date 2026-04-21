import os
from dotenv import load_dotenv
from supabase import create_client

from sharepoint_sync import get_global_ops_map, smart_find_op_numero

load_dotenv()
db_maps = get_global_ops_map()
map_str, map_id, map_id_to_op = db_maps

print(f"Is 7041 in map_id_to_op? {7041 in map_id_to_op}")
if 7041 in map_id_to_op:
    print(f"Value for 7041: {map_id_to_op[7041]}")

res = smart_find_op_numero('7041', db_maps)
print(f"smart_find_op_numero('7041') -> {res}")
