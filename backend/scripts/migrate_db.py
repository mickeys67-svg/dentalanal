import os
from sqlalchemy import create_engine, text

# Direct connection URL (Supabase default port 5432)
# Project: uujxtnvpqdwcjqhsoshi
# Pwd: 3AiLcoNojCHgZpTw
db_url = "postgresql://postgres:3AiLcoNojCHgZpTw@db.uujxtnvpqdwcjqhsoshi.supabase.co:5432/postgres"

print(f"--- Connecting Directly to Supabase (5432) ---")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("[CHECK] metrics_daily table...")
        
        # Check 'source' column
        col_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'metrics_daily' AND column_name = 'source');")).fetchone()[0]
        if not col_exists:
            print("[MIGRATE] Adding 'source' column...")
            conn.execute(text("ALTER TABLE metrics_daily ADD COLUMN source VARCHAR DEFAULT 'API';"))
            print("[OK] Column 'source' added.")
        else:
            print("[SKIP] Column 'source' already exists.")

        # Check 'revenue' column
        rev_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'metrics_daily' AND column_name = 'revenue');")).fetchone()[0]
        if not rev_exists:
            print("[MIGRATE] Adding 'revenue' column...")
            conn.execute(text("ALTER TABLE metrics_daily ADD COLUMN revenue FLOAT DEFAULT 0.0;"))
            print("[OK] Column 'revenue' added.")
        
        conn.commit()
    print("--- Migration Success! ---")
except Exception as e:
    print(f"--- Migration Failed: {e} ---")

if __name__ == "__main__":
    pass
