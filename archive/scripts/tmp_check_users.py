import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

try:
    res = supabase.table("perfiles").select("*").execute()
    with open("tmp_users_out.txt", "w") as f:
        f.write("Usuarios en perfiles:\n")
        for u in res.data:
            f.write(f"ID: {u.get('id')}, username: {u.get('username')}, nombre: {u.get('nombre')}, apellido: {u.get('apellido')}, role_id: {u.get('role_id')}\n")
        f.write("\n")
    print("Done")
except Exception as e:
    print("❌ Error query:", e)
