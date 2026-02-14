import os
from sqlalchemy import create_engine, text

# Try Pooler with Options
urls = [
    "postgresql://postgres.uujxtnvpqdwcjqhsoshi:3AiLcoNojCHgZpTw@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require&options=project=uujxtnvpqdwcjqhsoshi",
    "postgresql://postgres:3AiLcoNojCHgZpTw@db.uujxtnvpqdwcjqhsoshi.supabase.co:5432/postgres",
    "postgresql://postgres.uujxtnvpqdwcjqhsoshi:3AiLcoNojCHgZpTw@aws-0-us-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
]

for url in urls:
    print(f"\n--- Testing: {url.split('@')[-1]} ---")
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 5})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).fetchone()
            print(f"SUCCESS: {res}")
            break
    except Exception as e:
        print(f"FAILED: {str(e)[:100]}")
