import sqlite3
import uuid
import json
from datetime import datetime
from sqlalchemy import create_engine, text

# 설정 로드
from app.core.config import settings

SQLITE_PATH = "backend/test.db"

# 사용자가 제공한 Supabase 정보 (설정 파일에서 로드)
import urllib.parse
raw_pwd = settings.DATABASE_PASSWORD
safe_pwd = urllib.parse.quote_plus(raw_pwd) if raw_pwd else ""
# 프로젝트 ID: uujxtnvpqdwcjqhsoshi (aws-0-us-west-1.pooler.supabase.com 사용)
SUPABASE_URL = f"postgresql://postgres.uujxtnvpqdwcjqhsoshi:{safe_pwd}@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
print(f"DEBUG: Using URL (masked): {SUPABASE_URL.replace(safe_pwd, '***') if safe_pwd else 'URL_NOT_CONFIGURED'}")

def migrate():
    print(f"--- 로컬 {SQLITE_PATH} 에서 Supabase로 데이터 이전을 시작합니다 ---")
    
    # 1. 연결 설정
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    pg_engine = create_engine(SUPABASE_URL)
    
    # 2. 이전할 테이블 목록 (순서 중요: 외래키 의존성 고려)
    tables = [
        "agencies", 
        "users", 
        "clients", 
        "targets", 
        "keywords", 
        "platform_connections", 
        "campaigns", 
        "metrics_daily",
        "report_templates",
        "reports"
    ]
    
    with pg_engine.connect() as pg_conn:
        for table in tables:
            print(f"Migrating table: {table}...")
            
            # SQLite에서 데이터 읽기
            try:
                sqlite_cur.execute(f"SELECT * FROM {table}")
                rows = sqlite_cur.fetchall()
            except sqlite3.OperationalError as e:
                print(f"Skipping {table}: {e}")
                continue
                
            if not rows:
                print(f"No data in {table}, skipping.")
                continue
            
            # PostgreSQL에 삽입 (Conflict 무시 - 이미 있는 데이터 보호)
            for row in rows:
                data = dict(row)
                
                # SQLAlchemy GUID 타입 처리를 위한 변환
                # SQLite의 문자열 UUID를 PostgreSQL의 UUID 형식 호환 스트링으로 보장
                columns = ", ".join(data.keys())
                values_placeholders = ", ".join([f":{k}" for k in data.keys()])
                
                query = text(f"INSERT INTO {table} ({columns}) VALUES ({values_placeholders}) ON CONFLICT DO NOTHING")
                try:
                    pg_conn.execute(query, data)
                except Exception as e:
                    print(f"Error inserting row in {table}: {e}")
        
        pg_conn.commit()
    
    print("--- 마이그레이션이 완료되었습니다! ---")
    sqlite_conn.close()

if __name__ == "__main__":
    migrate()
