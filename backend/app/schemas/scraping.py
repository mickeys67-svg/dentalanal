from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ScrapeRequest(BaseModel):
    keyword: str
    hospital_name: Optional[str] = None

class ScrapeResponse(BaseModel):
    task_id: str
    message: str

class PlaceResultItem(BaseModel):
    rank: int
    name: str
    address: Optional[str] = None
    keyword: str
    created_at: datetime

class ViewResultItem(BaseModel):
    rank: int
    title: str
    blog_name: str
    link: str
    keyword: str
    created_at: datetime
    
class SOVAnalysisRequest(BaseModel):
    target_hospital: str
    keywords: List[str]
    platform: str = "NAVER_PLACE" # "NAVER_PLACE" or "NAVER_VIEW"
    top_n: int = 5 # Default 5, configurable 1-20

class RankingRequest(BaseModel):
    keyword: str
    platform: str # "NAVER_PLACE" or "NAVER_VIEW"

class RankingResultItem(BaseModel):
    rank: int
    title: str # map from name for Place
    blog_name: Optional[str] = None
    link: Optional[str] = None
    created_at: datetime
    
class CompetitorAnalysisRequest(BaseModel):
    keyword: str
    platform: str # "NAVER_PLACE" or "NAVER_VIEW"
    top_n: int = 10

class CompetitorRankItem(BaseModel):
    name: str
    rank_count: int
    avg_rank: float
    share: float # Percentage of presence in top N

class CompetitorAnalysisResult(BaseModel):
    keyword: str
    platform: str
    top_n: int
    competitors: List[CompetitorRankItem]

class AIAnalysisRequest(BaseModel):
    keyword: str
    target_hospital: str
    platform: str = "NAVER_PLACE"
    top_n: int = 10

class AIAnalysisResponse(BaseModel):
    report: str

class SOVAnalysisResult(BaseModel):
    keyword: str
    total_items: int
    target_hits: int
    sov_score: float # Percentage
    top_rank: Optional[int] = None
