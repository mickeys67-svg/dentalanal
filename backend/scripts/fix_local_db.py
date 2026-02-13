import sqlite3
import os

def fix_sqlite_schema():
    db_path = "e:\\dentalanal\\backend\\test.db"
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist in platform_connections
        cursor.execute("PRAGMA table_info(platform_connections)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "access_token" not in columns:
            print("Adding access_token to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN access_token VARCHAR(500)")
        if "refresh_token" not in columns:
            print("Adding refresh_token to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN refresh_token VARCHAR(500)")
        if "token_expires_at" not in columns:
            print("Adding token_expires_at to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN token_expires_at DATETIME")
        if "account_name" not in columns:
            print("Adding account_name to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN account_name VARCHAR(255)")
        if "account_id" not in columns:
            print("Adding account_id to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN account_id VARCHAR(255)")
        if "created_at" not in columns:
            print("Adding created_at to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN created_at DATETIME")
        if "updated_at" not in columns:
            print("Adding updated_at to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN updated_at DATETIME")
        if "status" not in columns:
            print("Adding status to platform_connections")
            cursor.execute("ALTER TABLE platform_connections ADD COLUMN status VARCHAR(50)")
            
        # Check metrics_daily for source and meta_info
        cursor.execute("PRAGMA table_info(metrics_daily)")
        cols_metrics = [row[1] for row in cursor.fetchall()]
        if "source" not in cols_metrics:
            print("Adding source to metrics_daily")
            cursor.execute("ALTER TABLE metrics_daily ADD COLUMN source VARCHAR DEFAULT 'API'")
        if "meta_info" not in cols_metrics:
            print("Adding meta_info to metrics_daily")
            cursor.execute("ALTER TABLE metrics_daily ADD COLUMN meta_info JSON")
            
        conn.commit()
        print("Schema fixed successfully.")
    except Exception as e:
        print(f"Error fixing schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_sqlite_schema()
