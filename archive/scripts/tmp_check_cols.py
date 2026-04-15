import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

try:
    # Intento de select incluyendo numero_celular
    res = supabase.table("perfiles").select("id, numero_celular, whatsapp_habilitado").limit(1).execute()
    print("✅ Columns exist:", res.data)
except Exception as e:
    print("❌ Error query:", e)
