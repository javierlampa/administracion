import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Try to get one row to see columns
try:
    res = supabase.table('ordenes_publicidad').select('*').limit(1).execute()
    if res.data:
        cols = list(res.data[0].keys())
        print("COLUMNS LIST:")
        for c in cols:
            print(f"- {c}")
    else:
        print("No data found in v_todas_las_op_report")
except Exception as e:
    print("Error:", e)
