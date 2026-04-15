import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

for view in ["v_pagos_resumen", "v_comisiones_report"]:
    try:
        res = supabase.table(view).select("*").limit(1).execute()
        if res.data:
            print(f"\nColumnas en {view}:")
            for col in sorted(res.data[0].keys()):
                print(f"- {col}")
        else:
            print(f"\n{view} no tiene datos.")
    except Exception as e:
        print(f"\nError en {view}: {e}")
