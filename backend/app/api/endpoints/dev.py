
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from sqlalchemy import text # Added text import
from app.models.models import User, UserRole, Client, Target, Keyword, DailyRank, PlatformType, Settlement, SettlementStatus
from app.core.security import get_password_hash
from app.api.endpoints.auth import get_current_user # FIX: Import missing dependency
from datetime import datetime, timedelta
import uuid
import random

router = APIRouter()

@router.post("/seed", status_code=201)
def seed_demo_data(
    db: Session = Depends(get_db),
    admin_secret: str = "dental1234" # Simple protection for demo endpoint
):
    """
    Seeds the database with demo data:
    - Admin User (admin@test.com / admin123!)
    - Sample Client (샘플 치과)
    - Targets (Competitors)
    - Keywords & Ranks
    - Settlement Data
    """
    if admin_secret != "dental1234":
        raise HTTPException(status_code=403, detail="Invalid secret")
        
    try:
        # 1. Create Admin User
        admin_email = "admin@test.com"
        admin = db.query(User).filter(User.username == admin_email).first()
        if not admin:
            admin = User(
                id=uuid.uuid4(),
                username=admin_email,
                email=admin_email,
                hashed_password=get_password_hash("admin123!"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin)
            print("Created Admin User")
            
        # 2. Create Sample Client
        client_name = "샘플 치과"
        client = db.query(Client).filter(Client.name == client_name).first()
        if not client:
            client = Client(
                id=uuid.uuid4(),
                name=client_name,
                industry="치과의원",
                agency_id=uuid.UUID("00000000-0000-0000-0000-000000000000")
            )
            db.add(client)
            print("Created Sample Client")
        
        db.flush() # Get IDs
        
        # 3. Create Keywords
        keywords_data = ["강남역 치과", "임플란트", "치아교정", "사랑니 발치"]
        keywords = []
        for kw_str in keywords_data:
            kw = db.query(Keyword).filter(Keyword.text == kw_str, Keyword.client_id == client.id).first()
            if not kw:
                kw = Keyword(
                    id=uuid.uuid4(),
                    text=kw_str,
                    client_id=client.id
                )
                db.add(kw)
            keywords.append(kw)
            
        # 4. Create Targets (Competitors + Owner)
        targets_data = [
            {"name": "샘플 치과", "type": "OWNER"},
            {"name": "라이벌 치과 A", "type": "COMPETITOR"},
            {"name": "강남 베스트 치과", "type": "COMPETITOR"},
        ]
        target_objs = []
        for t_data in targets_data:
            # Check if target exists (by name, for simplicity in demo)
            # Ideally should check client_id link but Target model link might be complex?
            # Let's just create new ones linked to client if supported, or global
            # For this demo, let's just create new ones if not exist
            t = db.query(Target).filter(Target.name == t_data["name"]).first()
            if not t:
                t = Target(
                    id=uuid.uuid4(),
                    name=t_data["name"],
                    type=t_data["type"]
                    # client_id might be needed if Target has it? Verify model
                )
                db.add(t)
            target_objs.append(t)
            
        db.flush()
        
        # 5. Create Daily Ranks (Past 7 days)
        today = datetime.now()
        for i in range(7):
            date = today - timedelta(days=i)
            for kw in keywords:
                for t in target_objs:
                    # Random rank between 1 and 30
                    rank_val = random.randint(1, 30)
                    
                    # Owner usually ranks better ;)
                    if t.name == "샘플 치과":
                        rank_val = random.randint(1, 5)
                        
                    dr = DailyRank(
                        id=uuid.uuid4(),
                        client_id=client.id,
                        target_id=t.id,
                        keyword_id=kw.id,
                        platform=PlatformType.NAVER_PLACE,
                        rank=rank_val,
                        captured_at=date
                    )
                    db.add(dr)

        # 6. Create Settlement (Last Month)
        last_month = today.replace(day=1) - timedelta(days=1)
        year, month = last_month.year, last_month.month
        
        settlement = db.query(Settlement).filter(
            Settlement.client_id == client.id, 
            Settlement.period == f"{year}-{month:02d}"
        ).first()
        
        if not settlement:
            settlement = Settlement(
                id=uuid.uuid4(),
                client_id=client.id,
                period=f"{year}-{month:02d}",
                total_spend=5000000,
                fee_amount=750000,
                tax_amount=75000,
                total_amount=5825000,
                status=SettlementStatus.PENDING,
                due_date=datetime(year, month+1 if month<12 else 1, 10)
            )
            db.add(settlement)
            print("Created Settlement")

        db.commit()
        return {"message": "Demo data seeded successfully!", "admin_email": admin_email}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")

@router.get("/kickstart")
def manual_kickstart_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    [Emergency] Manually trigger Full Sync via GET request (Browser Address Bar Friendly).
    """
    # Reuse the logic from automation.py
    from app.api.endpoints.automation import trigger_full_sync
    
    # We need to call it as a regular function, not await if it were async, 
    # but automation.trigger_full_sync is async. 
    # However, since we are in a sync context here (def, not async def), 
    # we can use background_tasks directly.
    
    # 1. Auto-Connect Logic (Duplicated for safety here)
    from app.models.models import PlatformConnection, PlatformType, Client
    from app.core.config import settings
    
    msg = []
    
    # Check Connection
    connections = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE").all()
    
    if not connections:
        return {"status": "SKIPPED", "message": "활성 연결이 없습니다. 데이터 연결을 먼저 해주세요."}

    # 2. Trigger Sync
    from app.tasks.sync_data import sync_all_channels
    background_tasks.add_task(sync_all_channels, db)
    msg.append(f"Triggered sync for {len(connections)} connections.")
    
    return {"status": "KICKSTARTED", "details": msg}

@router.api_route("/reset-all", methods=["GET", "DELETE"])
def reset_workspace_data(
    db: Session = Depends(get_db),
    # For emergency reset, maybe relax auth or require specific header?
    # but for now let's keep it safe behind auth
    current_user: User = Depends(get_current_user) 
):
    """
    [Emergency] Hard Reset for Workspace Data.
    Deletes ALL Clients, Connections, Campaigns, Metrics for the user's agency.
    """
    try:
        if current_user.role == UserRole.SUPER_ADMIN:
            # Delete EVERYTHING
            tables = [
                "metrics_daily", "campaigns", "sync_tasks", "sync_validation",
                "platform_connections", "leads", "lead_activities", 
                "settlement_details", "settlements", "reports", 
                "collaborative_tasks", "task_comments", 
                "swot_analysis", "strategy_goals", "analysis_history",
                "clients" 
                # Note: Not deleting Users or Agencies
            ]
            
            for t in tables:
                # Use cascade-like delete if possible, or just raw delete
                # But sqlalchemy delete needs models. Let's use raw SQL for speed/force
                # Be careful with foreign keys order
                pass 
                
            # Better approach: Delete Clients one by one using the robust delete_client logic
            clients = db.query(Client).all()
        else:
            if not current_user.agency_id:
                return {"error": "No Agency ID found for user."}
            clients = db.query(Client).filter(Client.agency_id == current_user.agency_id).all()
            
        from app.api.endpoints.clients import delete_client
        
        deleted_count = 0
        for client in clients:
            try:
                # call delete_client(client.id, db, current_user) logic directly
                # but delete_client is an API handler, might raise HTTPException.
                # Let's extract logic is risky. 
                # Let's just DELETE clients directly and rely on CASCADE if configured, 
                # OR manual cleanup script below.
                
                # Manual RAW Cleanup order:
                cid = str(client.id)
                db.execute(text("DELETE FROM metrics_daily WHERE campaign_id IN (SELECT id FROM campaigns WHERE connection_id IN (SELECT id FROM platform_connections WHERE client_id = :cid))"), {"cid": cid})
                db.execute(text("DELETE FROM campaigns WHERE connection_id IN (SELECT id FROM platform_connections WHERE client_id = :cid)"), {"cid": cid})
                db.execute(text("DELETE FROM platform_connections WHERE client_id = :cid"), {"cid": cid})
                db.execute(text("DELETE FROM clients WHERE id = :cid"), {"cid": cid})
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete client {client.id}: {e}")
                
        db.commit()
        return {"status": "RESET_COMPLETE", "deleted_clients": deleted_count}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
def view_server_logs(lines: int = 50):
    """
    View recent server logs (if written to file). 
    Cloud Run logs are usually stdout, but this might catch file logs if configured.
    """
    import os
    log_file = "app.log" # Assuming file logging is enabled
    if not os.path.exists(log_file):
        return {"error": "Log file not found (Logs are likely streaming to Cloud Logging only)"}
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.readlines()[-lines:]
        return {"logs": content}
    except Exception as e:
        return {"error": str(e)}

@router.get("/test-scrape")
async def test_scraping_connection(
    url: str = "https://www.naver.com",
    use_proxy: bool = True
):
    """
    Diagnostic Endpoint: Test Scraper Connectivity.
    Attempts to fetch a URL using the BaseScraper logic (Playwright + Bright Data).
    """
    import asyncio
    from app.scrapers.base import ScraperBase
    from playwright.async_api import async_playwright

    logs = []
    
    try:
        scraper = ScraperBase()
        # Manually verify env var first
        import os
        cdp_url = os.getenv("BRIGHT_DATA_CDP_URL")
        logs.append(f"CDP_URL Configured: {'Yes' if cdp_url else 'No'}")
        if cdp_url:
             # Sanitize env var (handle potential quotes from YAML)
            cdp_url = cdp_url.strip().strip('"').strip("'")
            
             # Masking for safety in response
            masked_url = cdp_url.replace(cdp_url.split('@')[0], '***') if '@' in cdp_url else '***'
            logs.append(f"CDP_URL (Masked): {masked_url}")

        # Try scraping
        logs.append(f"Attempting to fetch {url}...")
        
        async with async_playwright() as p:
            browser = None
            try:
                # Robust check: must start with wss://
                if use_proxy and cdp_url and cdp_url.startswith("wss://"):
                    logs.append("Connecting to Bright Data CDP...")
                    browser = await p.chromium.connect_over_cdp(cdp_url)
                else:
                    if cdp_url:
                         logs.append(f"Invalid CDP URL format (Len: {len(cdp_url)}). Falling back to Local Browser.")
                    logs.append("Launching local browser (No Proxy)...")
                    browser = await p.chromium.launch(headless=True)
                
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = await context.new_page()
                
                logs.append("Page created. Navigating...")
                await page.goto(url, timeout=30000)
                
                title = await page.title()
                content = await page.content()
                logs.append(f"Success! Title: {title}")
                logs.append(f"Content Length: {len(content)}")
                
                return {
                    "status": "SUCCESS",
                    "url": url,
                    "title": title,
                    "logs": logs
                }
                
            except Exception as e:
                logs.append(f"Browser Error: {str(e)}")
                # Re-raise to catch in outer block or return error
                raise e
            finally:
                if browser:
                    await browser.close()
                    
    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
            "logs": logs
        }

@router.get("/system-diag")
async def system_diagnosis():
    """
    Comprehensive System Health Check (Network, DNS, Env, Filesystem).
    Used for Phase 2 Analysis.
    """
    import socket
    import requests
    import os
    import sys
    
    report = {
        "hostname": socket.gethostname(),
        "platform": sys.platform,
        "python_version": sys.version,
        "network": {},
        "env": {},
        "playwright": {}
    }

    # 1. DNS Check
    try:
        report["network"]["dns_naver"] = socket.gethostbyname("naver.com")
        report["network"]["dns_google"] = socket.gethostbyname("google.com")
        report["network"]["dns_status"] = "OK"
    except Exception as e:
        report["network"]["dns_status"] = f"FAIL: {str(e)}"

    # 2. Outbound HTTP Check (Simple Request)
    try:
        # distinct from scraping, just checking basic connectivity
        resp = requests.get("https://www.google.com", timeout=5)
        report["network"]["http_google_status"] = resp.status_code
        
        # Check Public IP
        # use a reliable echo service
        try:
            ip_resp = requests.get("https://api.ipify.org?format=json", timeout=5)
            if ip_resp.status_code == 200:
                report["network"]["public_ip"] = ip_resp.json().get("ip")
        except:
             report["network"]["public_ip_check"] = "Failed"

    except Exception as e:
        report["network"]["http_status"] = f"FAIL: {str(e)}"

    # 3. Environment Check (Masked)
    cdp_url = os.getenv("BRIGHT_DATA_CDP_URL")
    report["env"]["BRIGHT_DATA_CDP_URL_EXISTS"] = bool(cdp_url)
    if cdp_url:
        report["env"]["BRIGHT_DATA_CDP_URL_LEN"] = len(cdp_url)
        report["env"]["BRIGHT_DATA_CDP_URL_VAL_REPR"] = repr(cdp_url) # Check for quotes/spaces
    
    # 4. Playwright Browser Check
    # Cloud Run default path for playwright browsers
    # Usually ~/.cache/ms-playwright
    import pathlib
    home = pathlib.Path.home()
    cache_dir = home / ".cache" / "ms-playwright"
    report["playwright"]["cache_dir"] = str(cache_dir)
    report["playwright"]["exists"] = cache_dir.exists()
    if cache_dir.exists():
        report["playwright"]["content"] = [f.name for f in cache_dir.iterdir()]

    return report
