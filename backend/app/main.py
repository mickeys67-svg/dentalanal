from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import asyncio
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"Background startup: Database schema sync or seeding failed: {e}")

    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Background startup: Scheduler failed to start: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure critical startup tasks (DB init, seeding) are complete before accepting requests
    await run_startup_tasks()
    yield
    # Shutdown logic
    from app.core.scheduler import stop_scheduler
    try:
        stop_scheduler()
    except:
        pass

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
from app.api.endpoints import auth, scrape, analyze, dashboard, connectors, strategy, collaboration, automation, clients, users, status, reports, notifications, settlement
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
