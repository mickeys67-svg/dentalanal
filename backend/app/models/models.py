import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Enum, CHAR
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as string.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value
from app.core.database import Base

class TargetType(str, enum.Enum):
    OWNER = "OWNER"
    COMPETITOR = "COMPETITOR"
    OTHERS = "OTHERS"

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

class PlatformType(str, enum.Enum):
    NAVER_VIEW = "NAVER_VIEW"
    NAVER_PLACE = "NAVER_PLACE"
    NAVER_AD = "NAVER_AD"
    GOOGLE_ADS = "GOOGLE_ADS"
    META_ADS = "META_ADS"
    KAKAO_AD = "KAKAO_AD"

class Agency(Base):
    __tablename__ = "agencies"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    branding_config = Column(JSON, nullable=True) # {primary_color: "#...", ...}
    
    clients = relationship("Client", back_populates="agency")

class Client(Base):
    __tablename__ = "clients"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    agency_id = Column(GUID, ForeignKey("agencies.id"), nullable=False)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    
    agency = relationship("Agency", back_populates="clients")
    connections = relationship("PlatformConnection", back_populates="client")

class PlatformConnection(Base):
    __tablename__ = "platform_connections"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    credentials = Column(JSON, nullable=True) # encrypted or sensitive data
    status = Column(String, default="ACTIVE")
    
    client = relationship("Client", back_populates="connections")
    campaigns = relationship("Campaign", back_populates="connection")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    connection_id = Column(GUID, ForeignKey("platform_connections.id"), nullable=False)
    external_id = Column(String, nullable=True) # ID from the platform (Google/Meta ID)
    name = Column(String, nullable=False)
    status = Column(String, nullable=True)
    
    connection = relationship("PlatformConnection", back_populates="campaigns")
    metrics = relationship("MetricsDaily", back_populates="campaign")

class MetricsDaily(Base):
    __tablename__ = "metrics_daily"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    campaign_id = Column(GUID, ForeignKey("campaigns.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    spend = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    
    campaign = relationship("Campaign", back_populates="metrics")

# --- Legacy Labels (Keep for now to avoid breaking existing code) ---
class Target(Base):
    __tablename__ = "targets"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(Enum(TargetType), nullable=False)
    urls = Column(JSON, nullable=True)
    daily_ranks = relationship("DailyRank", back_populates="target")

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    term = Column(String, nullable=False)
    category = Column(String, nullable=True)
    daily_ranks = relationship("DailyRank", back_populates="keyword")

class DailyRank(Base):
    __tablename__ = "daily_ranks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    target_id = Column(GUID, ForeignKey("targets.id"), nullable=False)
    keyword_id = Column(GUID, ForeignKey("keywords.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    rank = Column(Integer, nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    target = relationship("Target", back_populates="daily_ranks")
    keyword = relationship("Keyword", back_populates="daily_ranks")

class ContentsMetric(Base):
    __tablename__ = "contents_metrics"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    url = Column(String, unique=True, nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)

class CrawlingLog(Base):
    __tablename__ = "crawling_logs"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    target_id = Column(GUID, ForeignKey("targets.id"), nullable=True)
    url = Column(String, nullable=False)
    status = Column(Integer, nullable=False) 
    response_body = Column(String, nullable=True) 
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- Strategy Models ---

class SWOTAnalysis(Base):
    __tablename__ = "swot_analyses"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id"), nullable=False)
    strengths = Column(JSON, nullable=True) # ["...", "..."]
    weaknesses = Column(JSON, nullable=True)
    opportunities = Column(JSON, nullable=True)
    threats = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

class StrategyGoal(Base):
    __tablename__ = "strategy_goals"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    smart_s = Column(String, nullable=True) # Specific
    smart_m = Column(String, nullable=True) # Measurable
    smart_a = Column(String, nullable=True) # Achievable
    smart_r = Column(String, nullable=True) # Relevant
    smart_t = Column(String, nullable=True) # Time-bound
    status = Column(String, default="IN_PROGRESS") # COMPLETED, ABANDONED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- Collaboration Models ---

class CollaborativeTask(Base):
    __tablename__ = "collaborative_tasks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, IN_PROGRESS, COMPLETED
    owner = Column(String, nullable=True)
    deadline = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    request_type = Column(String, nullable=True) # BUDGET, CREATIVE
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
