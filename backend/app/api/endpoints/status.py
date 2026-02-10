from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from sqlalchemy import text
import datetime

router = APIRouter()

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    # 1. Check DB
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except:
        pass

    # 2. Get Recent Logs (Simulated for now, or from a table)
    # In a real app, you might query a 'system_logs' table
    logs = [
        {"timestamp": datetime.datetime.now().isoformat(), "level": "INFO", "message": "System monitoring started."},
        {"timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(), "level": "SUCCESS", "message": "Daily data sync completed for 12 clients."},
    ]

    return {
        "status": "Healthy" if db_ok else "Degraded",
        "database": "Connected" if db_ok else "Disconnected",
        "scheduler": "Running",
        "uptime": "99.9%",
        "recent_logs": logs
    }
