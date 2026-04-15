import psycopg2
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("No DB URL")

# Let's bypass pooler and use python supabase client but calling an RPC?
# We can't.
# But wait! I have the URL. The pooler failed before with psycopg2. 
# But wait, python's psycopg2 failed because of the url.
