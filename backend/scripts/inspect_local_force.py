
import psycopg2
import os

# RE-VERIFIED from deploy.yml (xklppnykoeezgtxmomrl)
# Using Pooler Host (Standard for US West): aws-0-us-west-1.pooler.supabase.com
# User format for pooler: postgres.[project-ref]
# Password: From deploy.yml (2KJCvEbTrWjAjXH1)
# Port: 6543 (Transaction Mode)

DB_HOST = "aws-0-us-west-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.xklppnykoeezgtxmomrl" 
DB_PASS = "2KJCvEbTrWjAjXH1"
DB_PORT = "6543"

try:
    print(f"Connecting to {DB_HOST} as {DB_USER}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        sslmode="require"
    )
    cursor = conn.cursor()
    
    # Check system_configs
    print("Querying system_configs...")
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_configs');")
    exists = cursor.fetchone()[0]
    
    if exists:
        cursor.execute("SELECT key, value, description FROM system_configs;")
        rows = cursor.fetchall()
        print(f"\n[FOUND {len(rows)} CONFIGS]")
        for row in rows:
            print(f"Key: {row[0]}")
            print(f"Val: {row[1]}") # Value might be long
            print(f"Desc: {row[2]}")
            print("-" * 30)
            
            if "2446031" in str(row[1]):
                print("!!! CRITICAL MATCH FOUND: 2446031 IS HERE !!!")
    else:
        print("[TABLE NOT FOUND] system_configs does not exist.")
        
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Connection failed: {e}")
