import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("ordenes_publicidad").select("op").execute()
ops = [r['op'] for r in res.data]
from collections import Counter
c = Counter(ops)
dupes = {item: count for item, count in c.items() if count > 1}
print(f"Duplicate OPs count: {len(dupes)}")
if dupes:
    print("Samples:")
    for d, count in list(dupes.items())[:10]:
        print(f"  OP {d}: {count} times")
