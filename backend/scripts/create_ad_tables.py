import os
from sqlalchemy import create_engine, text

# Helper: Try multiple URLs from test_db_conn.py
db_urls = [
    "postgresql://postgres:3AiLcoNojCHgZpTw@db.uujxtnvpqdwcjqhsoshi.supabase.co:5432/postgres",
    "postgresql://postgres.uujxtnvpqdwcjqhsoshi:3AiLcoNojCHgZpTw@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require&options=project=uujxtnvpqdwcjqhsoshi",
    "postgresql://postgres.uujxtnvpqdwcjqhsoshi:3AiLcoNojCHgZpTw@aws-0-us-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
]

success = False
for i, db_url in enumerate(db_urls):
    print(f"\n[ATTEMPT {i+1}] Connecting to: {db_url.split('@')[-1]} ...")
    try:
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            print("[MIGRATE] Creating 'ad_groups' table...")
            conn.execute(text(ddl_ad_groups))
            print("[OK] 'ad_groups' checked/created.")

            print("[MIGRATE] Creating 'ad_keywords' table...")
            conn.execute(text(ddl_ad_keywords))
            print("[OK] 'ad_keywords' checked/created.")

            print("[MIGRATE] Creating 'ad_metrics_daily' table...")
            conn.execute(text(ddl_ad_metrics))
            print("[OK] 'ad_metrics_daily' checked/created.")
            
        print(f"--- Migration Success using URL #{i+1} ---")
        success = True
        break
    except Exception as e:
        print(f"[FAILED] URL #{i+1} Error: {e}")

if not success:
    print("\n--- ALL CONNECTIONS FAILED. CHECK NETWORK/DNS ---")
