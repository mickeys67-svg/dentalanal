import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class TargetType(str, enum.Enum):
    OWNER = "OWNER"
    COMPETITOR = "COMPETITOR"
    OTHERS = "OTHERS"

class PlatformType(str, enum.Enum):
    NAVER_VIEW = "NAVER_VIEW"
    NAVER_PLACE = "NAVER_PLACE"

class Target(Base):
    __tablename__ = "targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(Enum(TargetType), nullable=False)
    urls = Column(JSONB, nullable=True)
    
    daily_ranks = relationship("DailyRank", back_populates="target")

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term = Column(String, nullable=False)
    category = Column(String, nullable=True)

    daily_ranks = relationship("DailyRank", back_populates="keyword")

class DailyRank(Base):
    __tablename__ = "daily_ranks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("keywords.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    rank = Column(Integer, nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    target = relationship("Target", back_populates="daily_ranks")
    keyword = relationship("Keyword", back_populates="daily_ranks")

class ContentsMetric(Base):
    __tablename__ = "contents_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, unique=True, nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)

class CrawlingLog(Base):
    __tablename__ = "crawling_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=True)
    url = Column(String, nullable=False)
    status = Column(Integer, nullable=False) # HTTP Status
    response_body = Column(String, nullable=True) # Raw HTML (using String/Text for large content)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
