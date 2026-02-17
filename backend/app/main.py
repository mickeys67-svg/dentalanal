# [PROD] DentalAnal Backend API - Deployment v1.0.3 (Secrets Updated by User)
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import asyncio
import traceback
from app.core.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Sentry (Safe Import)
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

from app.core.config import settings

if sentry_sdk and settings.SENTRY_DSN:
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment="production"
        )
        logger.info("[Sentry] Monitoring Initialized")
    except Exception as e:
        logger.warning(f"[Sentry] Failed to initialize: {e}")
elif not sentry_sdk and settings.SENTRY_DSN:
    logger.warning("⚠️ SENTRY_DSN is set but sentry-sdk is not installed. Run 'pip install sentry-sdk[fastapi]'")

async def run_startup_tasks():
    # Lazy load to avoid top-level issues
    from app.core.database import engine, Base, SQLALCHEMY_DATABASE_URL
    from app.core.scheduler import start_scheduler
    import app.models.models # CRITICAL: Must import models to register with metadata
    import asyncio
    
    logger.info(f"Background startup: Initializing database tables with URL: {SQLALCHEMY_DATABASE_URL}")
    try:
        # Run synchronous DB operations in a thread pool to avoid blocking the event loop
        # This registers models and creates tables if they don't exist
        await asyncio.to_thread(Base.metadata.create_all, bind=engine)
        logger.info("Background startup: Database schema sync successful. Tables checked/created.")

        # [HOTFIX] Ensure metrics_daily has 'source' and 'revenue' columns (Self-Healing)
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                # 1. Check source column
                col_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'metrics_daily' AND column_name = 'source');")).fetchone()[0]
                if not col_exists:
                    logger.info("[MIGRATE] Adding 'source' column to metrics_daily...")
                    conn.execute(text("ALTER TABLE metrics_daily ADD COLUMN source VARCHAR DEFAULT 'API';"))
                
                # 3. Check revenue column
                rev_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'metrics_daily' AND column_name = 'revenue');")).fetchone()[0]
                if not rev_exists:
                    logger.info("[MIGRATE] Adding 'revenue' column to metrics_daily...")
                    conn.execute(text("ALTER TABLE metrics_daily ADD COLUMN revenue FLOAT DEFAULT 0.0;"))
                
                # 4. Check meta_info column
                meta_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'metrics_daily' AND column_name = 'meta_info');")).fetchone()[0]
                if not meta_exists:
                    logger.info("[MIGRATE] Adding 'meta_info' column to metrics_daily...")
                    conn.execute(text("ALTER TABLE metrics_daily ADD COLUMN meta_info JSONB;"))

                # 5. Check clients columns (created_at)
                client_created_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'clients' AND column_name = 'created_at');")).fetchone()[0]
                if not client_created_exists:
                    logger.info("[MIGRATE] Adding 'created_at' column to clients...")
                    conn.execute(text("ALTER TABLE clients ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                    conn.execute(text("ALTER TABLE clients ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))

                # 6. Check analysis_history columns
                hist_result_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'analysis_history' AND column_name = 'result_data');")).fetchone()[0]
                if not hist_result_exists:
                    logger.info("[MIGRATE] Adding 'result_data' column to analysis_history...")
                    conn.execute(text("ALTER TABLE analysis_history ADD COLUMN result_data JSONB;"))
                    conn.execute(text("ALTER TABLE analysis_history ADD COLUMN is_saved BOOLEAN DEFAULT FALSE;"))
                
                conn.commit()
                logger.info("[OK] database schema verified/patched.")
        except Exception as e:
            logger.error(f"Failed to run startup migration: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

        # SEEDING: Ensure default Agency and Admin exist
        from sqlalchemy.orm import Session
        from app.models.models import Agency, User, UserRole, ReportTemplate
        from app.core.security import get_password_hash
        
        with Session(engine) as session:
            # 1. Ensure Default Agency exists
            agency_id = "00000000-0000-0000-0000-000000000000"
            agency = session.query(Agency).filter(Agency.id == agency_id).first()
            if not agency:
                agency = Agency(id=agency_id, name="D-MIND Default Agency")
                session.add(agency)
                logger.info("Seeding: Default Agency created.")
            
            # 2. Ensure Default Admin User exists
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@dmind.com")
            admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123!")
            admin = session.query(User).filter(User.email == admin_email).first()
            if not admin:
                admin = User(
                    email=admin_email,
                    hashed_password=get_password_hash(admin_pw),
                    name="Administrator",
                    role=UserRole.ADMIN,
                    agency_id=agency_id
                )
                session.add(admin)
                logger.info(f"Seeding: Default Admin User ({admin_email}) created.")
            
            # 3. Ensure Executive Dashboard Template exists
            template_name = "Executive Dashboard"
            template = session.query(ReportTemplate).filter(ReportTemplate.name == template_name).first()
            if not template:
                template = ReportTemplate(
                    name=template_name,
                    description="경영진을 위한 핵심 마케팅 지표 요약 리포트",
                    config={
                        "layout": "grid",
                        "widgets": [
                            {"id": "kpi_summary", "type": "KPI_GROUP", "metrics": ["spend", "impressions", "clicks", "conversions"]},
                            {"id": "funnel_chart", "type": "FUNNEL", "title": "전환 퍼널 분석"},
                            {"id": "roi_tracking", "type": "LINE_CHART", "title": "ROAS 추이"},
                            {"id": "market_bench", "type": "BENCHMARK", "title": "업종 평균 지표 비교"},
                            {"id": "ai_insight", "type": "AI_DIAGNOSIS", "title": "Gemini AI 성과 진단 리포트"}
                        ]
                    }
                )
                session.add(template)
                logger.info("Seeding: Executive Dashboard Template created.")
            
            session.commit()
    except Exception as e:
        logger.error(f"Background startup: Critical failure in schema sync/seeding: {e}")
        # Even if this fails, we want the server to stay alive to serve /health
        # and allow manual diagnosis or self-healing config updates.
        import traceback
        logger.error(traceback.format_exc())

    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Background startup: Scheduler failed to start: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # CRITICAL: Start the port listener IMMEDIATELY by not awaiting heavy tasks here
    # We create a background task for initialization to avoid Cloud Run Startup Timeout
    init_task = asyncio.create_task(run_startup_tasks())
    
    yield
    
    # Shutdown logic
    from app.core.scheduler import stop_scheduler
    try:
        stop_scheduler()
    except Exception as e:
        logger.error(f"Startup task failed: {e}")
    if not init_task.done():
        init_task.cancel()

app = FastAPI(title="D-MIND API", version="1.0.0", lifespan=lifespan)

# CORS Configuration
origins = [
    "https://dentalanal-864421937037.us-west1.run.app",
    "https://dentalanal-backend-864421937037.us-west1.run.app",
    "https://dentalanal-2556cvhe3q-uw.a.run.app",
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoint - CRITICAL for Cloud Run
@app.get("/healthz")
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Lazy-loaded Routers to prevent top-level import crashes
from app.api.endpoints import auth, scrape, analyze, dashboard, connectors, strategy, collaboration, automation, clients, users, status, reports, notifications, settlement, competitors, roi_optimization, trends
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(status.router, prefix="/api/v1/status", tags=["Status"])
app.include_router(scrape.router, prefix="/api/v1/scrape", tags=["Scraping"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connectors"])
app.include_router(strategy.router, prefix="/api/v1/strategy", tags=["Strategy"])
app.include_router(collaboration.router, prefix="/api/v1/collaboration", tags=["Collaboration"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["Automation"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(settlement.router, prefix="/api/v1/settlement", tags=["Settlement"])
app.include_router(competitors.router, prefix="/api/v1/competitors", tags=["Competitor Intelligence"])
app.include_router(roi_optimization.router, prefix="/api/v1/roi", tags=["ROI Optimization"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["Trend Analysis"])

@app.get("/")
def read_root():
    return {"message": "D-MIND API Service is running", "version": "1.0.0"}

# Catch-all for 404 Debugging
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, path_name: str):
    logger.warning(f"404 NOT FOUND: {request.method} {path_name}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"엔드포인트를 찾을 수 없습니다: {path_name}", "path": path_name}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error Catch: {exc}")
    logger.error(traceback.format_exc())
    
    # Manual CORS headers for error responses
    headers = {
        "Access-Control-Allow-Origin": "*", # In error state, allow all to let browser see it
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"내부 서버 오류가 발생했습니다: {str(exc)}",
            "error_type": str(type(exc).__name__),
            "traceback": traceback.format_exc()
        },
        headers=headers
    )
