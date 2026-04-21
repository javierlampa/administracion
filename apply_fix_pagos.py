import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service_role key

with open("database/sql/22_FIX_PAGOS_JOIN_BY_OP_NUMERO.sql", "r", encoding="utf-8") as f:
    sql = f.read()

# Usar el endpoint REST de Supabase para ejecutar SQL via la funcion exec_sql (si existe)
# O mejor, usar el Management API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Intentar via RPC si hay una función exec_sql
resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
    headers=headers,
    json={"sql_query": sql}
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
