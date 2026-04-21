import os
from dotenv import load_dotenv
from supabase import create_client

from sharepoint_sync import get_global_ops_map

load_dotenv()
db_maps = get_global_ops_map()
map_str, map_id, map_id_to_op = db_maps

print(f"'7041' in map_str: {'7041' in map_str}")
if '7041' in map_str:
    print(f"map_str['7041'] (id associated with this text): {map_str['7041']}")
