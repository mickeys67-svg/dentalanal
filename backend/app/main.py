from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import asyncio

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
    except Exception as e:
        logger.error(f"Background startup: Database schema sync failed: {e}")

    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Background startup: Scheduler failed to start: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start startup tasks in the background so uvicorn can start listening immediately
    asyncio.create_task(run_startup_tasks())
    yield
    # Shutdown logic
    from app.core.scheduler import stop_scheduler
    try:
        stop_scheduler()
    except:
        pass

app = FastAPI(title="D-MIND API", version="1.0.0", lifespan=lifespan)

# CORS Configuration
origins = ["*"]
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
from app.api.endpoints import scrape, analyze, dashboard, connectors, strategy, collaboration, automation, clients
app.include_router(scrape.router, prefix="/api/v1/scrape", tags=["Scraping"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connectors"])
app.include_router(strategy.router, prefix="/api/v1/strategy", tags=["Strategy"])
app.include_router(collaboration.router, prefix="/api/v1/collaboration", tags=["Collaboration"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["Automation"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients"])

@app.get("/")
def read_root():
    return {"message": "Welcome to D-MIND API"}
