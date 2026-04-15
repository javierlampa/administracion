import os
from supabase import create_client
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

load_dotenv('.env')

# Obteniendo la conexion de DB si tenemos una string POSTGRESQL (Supabase suele proveerla)
# Como Python no tiene un metodo "DROP CONSTRAINT" directo por REST/Postgrest, 
# usaremos las sentencias a traves del SQL Editor o te paso el codigo exacto.

print("Debes ir al SQL Editor de Supabase y correr:")
print("ALTER TABLE pagos DROP CONSTRAINT IF EXISTS pagos_op_id_fkey;")
print("ALTER TABLE pagos DROP CONSTRAINT IF EXISTS fk_pagos_op;")
print("ALTER TABLE tv DROP CONSTRAINT IF EXISTS fk_tv_op;")
print("ALTER TABLE unidades_negocio DROP CONSTRAINT IF EXISTS fk_unn_op;")
