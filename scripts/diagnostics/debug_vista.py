import os, sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    res = supabase.table("v_pagos_resumen").select("*").limit(1).execute()
    print("Success:", res.data)
except Exception as e:
    print("EXCEPTION OCCURRED:", e)
