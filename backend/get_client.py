from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:736567@db.uujxtnvpqdwcjqhsoshi.supabase.co:5432/postgres')
with engine.connect() as conn:
    result = conn.execute(text('SELECT id FROM clients LIMIT 1;'))
    row = result.fetchone()
    if row:
        print(row[0])
