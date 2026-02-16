from sqlalchemy import create_engine, text

# Use Direct Connection URL (Supabase)
DB_URL = "postgresql://postgres:2KJCvEbTrWjAjXH1@db.xklppnykoeezgtxmomrl.supabase.co:5432/postgres?sslmode=require"
# Alternate URL if above fails (Pooler)
# DB_URL = "postgresql://postgres.uujxtnvpqdwcjqhsoshi:3AiLcoNojCHgZpTw@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(DB_URL)

def purge_system_configs():
    print("--- Purging system_configs table ---")
    try:
        with engine.connect() as conn:
            # Check if table exists
            exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_configs');")).fetchone()[0]
            if exists:
                conn.execute(text("TRUNCATE TABLE system_configs;"))
                conn.commit()
                print("[SUCCESS] All data in `system_configs` has been deleted.")
            else:
                print("[SKIP] Table `system_configs` does not exist.")
    except Exception as e:
        print(f"[ERROR] Failed to purge: {e}")

if __name__ == "__main__":
    purge_system_configs()
