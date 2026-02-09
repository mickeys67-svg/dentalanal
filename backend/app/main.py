from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import scrape, analyze

app = FastAPI(title="D-MIND API", version="1.0.0")

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*", # Allow all origins for Cloud Run deployment (or add specific URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape.router, prefix="/api/v1/scrape", tags=["Scraping"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analysis"])

@app.get("/")
def read_root():
    return {"message": "Welcome to D-MIND API"}
