import os
import requests
import msal
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Config
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get Site ID
res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
site_id = res_site["value"][0]["id"]

# Get Top 10 expensive payments from SharePoint
url_pagos = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=20&$orderby=fields/ImportePago desc"
items = requests.get(url_pagos, headers=headers).json()["value"]

# Connect to DB
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print(f"{'SP_ID':<8} | {'OP':<10} | {'SP_Importe':>12} | {'DB_Importe':>12} | {'Diff':>12}")
print("-" * 65)

for i in items:
    f = i["fields"]
    sp_id = f["id"]
    sp_op = f.get("OP", f.get("OPLookupId", "N/A"))
    sp_val = float(f.get("ImportePago", 0))
    
    # Check in DB by ID (since we use SP ID as PK in pagos)
    db_res = supabase.table("pagos").select("importe_pago, op_numero").eq("id", sp_id).execute()
    if db_res.data:
        db_val = float(db_res.data[0]["importe_pago"] or 0)
        db_op = db_res.data[0]["op_numero"]
        diff = sp_val - db_val
        print(f"{sp_id:<8} | {str(sp_op):<10} | {sp_val:>12.2f} | {db_val:>12.2f} | {diff:>12.2f}")
    else:
        print(f"{sp_id:<8} | {str(sp_op):<10} | {sp_val:>12.2f} | {'Missing':>12} | {'-':>12}")
