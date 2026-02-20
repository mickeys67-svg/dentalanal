import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Date, JSON, Enum, CHAR, Text, Boolean
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

class SystemConfig(Base):
    """프로젝트의 전역 설정을 DB에 영구 보존하기 위한 테이블"""
    __tablename__ = "system_configs"
    key = Column(String(100), primary_key=True) # e.g., 'NAVER_AD_ACCESS_LICENSE'
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
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
    users = relationship("User", back_populates="agency")

class User(Base):
    __tablename__ = "users"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Integer, default=1)
    birth_date = Column(String, nullable=True) # YYYY-MM-DD
    agency_id = Column(GUID, ForeignKey("agencies.id"), nullable=True)
    
    agency = relationship("Agency", back_populates="users")

class Client(Base):
    __tablename__ = "clients"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    agency_id = Column(GUID, ForeignKey("agencies.id"), nullable=False)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    email = Column(String(255), nullable=True)          # 리포트 수신 이메일
    conversion_value = Column(Float, nullable=True)     # 전환당 수익 (기본 150,000원)
    fee_rate = Column(Float, nullable=True)             # 대행 수수료율 (기본 0.15 = 15%)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    agency = relationship("Agency", back_populates="clients")
    connections = relationship("PlatformConnection", back_populates="client", cascade="all, delete-orphan")
    swot_analyses = relationship("SWOTAnalysis", back_populates="client", cascade="all, delete-orphan")
    strategy_goals = relationship("StrategyGoal", back_populates="client", cascade="all, delete-orphan")
    tasks = relationship("CollaborativeTask", back_populates="client", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="client", cascade="all, delete-orphan")
    settlements = relationship("Settlement", back_populates="client", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="client", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="client", cascade="all, delete-orphan")
    analysis_history = relationship("AnalysisHistory", back_populates="client", cascade="all, delete-orphan")
    analytics_cache = relationship("AnalyticsCache", back_populates="client", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="client", cascade="all, delete-orphan")
    daily_ranks = relationship("DailyRank", back_populates="client", cascade="all, delete-orphan")

class PlatformConnection(Base):
    __tablename__ = "platform_connections"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    credentials = Column(JSON, nullable=True) # encrypted or sensitive data
    access_token = Column(String(500), nullable=True)
    refresh_token = Column(String(500), nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    account_name = Column(String(255), nullable=True)
    account_id = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1) # 1 for True, 0 for False (SQLite compatibility)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    client = relationship("Client", back_populates="connections")
    campaigns = relationship("Campaign", back_populates="connection", cascade="all, delete-orphan")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    connection_id = Column(GUID, ForeignKey("platform_connections.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, nullable=True) # ID from the platform (Google/Meta ID)
    name = Column(String, nullable=False)
    status = Column(String, nullable=True)
    
    connection = relationship("PlatformConnection", back_populates="campaigns")
    metrics = relationship("MetricsDaily", back_populates="campaign", cascade="all, delete-orphan")
    ad_groups = relationship("AdGroup", back_populates="campaign", cascade="all, delete-orphan")

class AdGroup(Base):
    """Represents a Naver Ad Group under a Campaign."""
    __tablename__ = "ad_groups"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    campaign_id = Column(GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, unique=True, nullable=False) # Naver AdGroup ID (nccAdgroupId)
    name = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    campaign = relationship("Campaign", back_populates="ad_groups")
    keywords = relationship("AdKeyword", back_populates="ad_group", cascade="all, delete-orphan")
    metrics = relationship("AdMetricsDaily", back_populates="ad_group", cascade="all, delete-orphan")

class AdKeyword(Base):
    """Represents a specific Keyword under an Ad Group."""
    __tablename__ = "ad_keywords"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    ad_group_id = Column(GUID, ForeignKey("ad_groups.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, unique=True, nullable=False) # Naver Keyword ID (nccKeywordId)
    text = Column(String, nullable=False) # The actual keyword text (e.g., '임플란트')
    bid_amt = Column(Integer, default=0) # Current bid amount
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ad_group = relationship("AdGroup", back_populates="keywords")
    metrics = relationship("AdMetricsDaily", back_populates="keyword", cascade="all, delete-orphan")

class AdMetricsDaily(Base):
    """
    Unified daily metrics for granular entities (AdGroup, Keyword).
    Polymorphic-like design: links to either AdGroup OR Keyword.
    """
    __tablename__ = "ad_metrics_daily"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    
    # Association (One must be set)
    ad_group_id = Column(GUID, ForeignKey("ad_groups.id", ondelete="CASCADE"), nullable=True)
    keyword_id = Column(GUID, ForeignKey("ad_keywords.id", ondelete="CASCADE"), nullable=True)
    
    # Core Metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    
    # Computed Metrics (Stored for fast read/sorting)
    ctr = Column(Float, default=0.0) # (clicks / impressions) * 100
    cpc = Column(Float, default=0.0) # spend / clicks
    roas = Column(Float, default=0.0) # (revenue / spend) * 100 (Revenue logic needed later)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ad_group = relationship("AdGroup", back_populates="metrics")
    keyword = relationship("AdKeyword", back_populates="metrics")

class MetricsDaily(Base):
    __tablename__ = "metrics_daily"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    campaign_id = Column(GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    spend = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    source = Column(String, default="API") # 'API', 'SCRAPER', 'RECONCILED'
    meta_info = Column(JSON, nullable=True) # Extra info like raw response snippet
    
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
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True)  # [Fix] Added owner
    term = Column(String, nullable=False)
    category = Column(String, nullable=True)
    daily_ranks = relationship("DailyRank", back_populates="keyword")
    client = relationship("Client", back_populates="keywords")

class DailyRank(Base):
    __tablename__ = "daily_ranks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True)  # [Fix] Added owner
    target_id = Column(GUID, ForeignKey("targets.id"), nullable=False)
    keyword_id = Column(GUID, ForeignKey("keywords.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    rank = Column(Integer, nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    target = relationship("Target", back_populates="daily_ranks")
    keyword = relationship("Keyword", back_populates="daily_ranks")
    client = relationship("Client", back_populates="daily_ranks")

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
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    strengths = Column(JSON, nullable=True) # ["...", "..."]
    weaknesses = Column(JSON, nullable=True)
    opportunities = Column(JSON, nullable=True)
    threats = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())
    
    client = relationship("Client", back_populates="swot_analyses")

class StrategyGoal(Base):
    __tablename__ = "strategy_goals"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    smart_s = Column(String, nullable=True) # Specific
    smart_m = Column(String, nullable=True) # Measurable
    smart_a = Column(String, nullable=True) # Achievable
    smart_r = Column(String, nullable=True) # Relevant
    smart_t = Column(String, nullable=True) # Time-bound
    status = Column(String, default="IN_PROGRESS") # COMPLETED, ABANDONED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="strategy_goals")

# --- Collaboration Models ---

class CollaborativeTask(Base):
    __tablename__ = "collaborative_tasks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="PENDING") # PENDING, IN_PROGRESS, COMPLETED
    owner = Column(String, nullable=True)
    deadline = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")

class TaskComment(Base):
    __tablename__ = "task_comments"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID, ForeignKey("collaborative_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    task = relationship("CollaborativeTask", back_populates="comments")
    user = relationship("User")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    requester_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    requester = relationship("User")
    client = relationship("Client", back_populates="approval_requests")

class Notice(Base):
    __tablename__ = "notices"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    agency_id = Column(GUID, ForeignKey("agencies.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    is_pinned = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    author = relationship("User")

class ReportTemplate(Base):
    __tablename__ = "report_templates"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    agency_id = Column(GUID, ForeignKey("agencies.id"), nullable=True) # templates can be global (null) or agency-specific
    config = Column(JSON, nullable=False) # Layout, charts, metrics mapping
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Report(Base):
    __tablename__ = "reports"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    # Only include columns that actually exist in the database
    # Removed: template_id, title, data, status, generated_at, schedule, created_at, updated_at
    # These are not present in the current Supabase schema

    client = relationship("Client")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=True)
    link = Column(String, nullable=True)
    is_read = Column(Integer, default=0) # 0 for False, 1 for True
    type = Column(String, nullable=True) # TASK, COMMENT, APPROVAL, NOTICE
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class SettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class Settlement(Base):
    __tablename__ = "settlements"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    period = Column(String, nullable=False) # e.g., "2024-02"
    total_spend = Column(Float, default=0.0)
    fee_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    status = Column(Enum(SettlementStatus), default=SettlementStatus.PENDING)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client")
    details = relationship("SettlementDetail", back_populates="settlement", cascade="all, delete-orphan")

class SettlementDetail(Base):
    __tablename__ = "settlement_details"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    settlement_id = Column(GUID, ForeignKey("settlements.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    campaign_name = Column(String, nullable=True)
    spend = Column(Float, default=0.0)
    fee_rate = Column(Float, default=0.0) # e.g., 0.15 for 15%
    fee_amount = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    settlement = relationship("Settlement", back_populates="details")

# --- Analytics Expansion (Adriel Benchmark Phase 1) ---

class Lead(Base):
    """Represents a potential patient or customer for the clinic."""
    __tablename__ = "leads"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    first_visit_date = Column(DateTime, nullable=False, server_default=func.now())
    cohort_month = Column(String(7), nullable=False) # e.g., '2024-01'
    channel = Column(String(50), nullable=True) # organic, paid, social, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="leads")
    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")
    profile = relationship("LeadProfile", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")

class LeadActivity(Base):
    """Aggregated monthly activity for a lead."""
    __tablename__ = "lead_activities"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    lead_id = Column(GUID, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    activity_month = Column(String(7), nullable=False) # '2024-02'
    visits = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("Lead", back_populates="activities")

class LeadProfile(Base):
    """Detailed characteristics for segment analysis."""
    __tablename__ = "lead_profiles"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    lead_id = Column(GUID, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    device_type = Column(String(20), nullable=True) # mobile, desktop
    region = Column(String(50), nullable=True) # Gangnam, etc.
    user_type = Column(String(20), nullable=True) # new, returning
    first_conversion_date = Column(DateTime, nullable=True)
    last_visit_date = Column(DateTime, nullable=True)
    total_visits = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    
    lead = relationship("Lead", back_populates="profile")

class LeadEvent(Base):
    """Granular touchpoint events for attribution & journey analysis."""
    __tablename__ = "lead_events"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    lead_id = Column(GUID, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False) # visit, click, conversion
    platform = Column(Enum(PlatformType), nullable=True)
    segment_tags = Column(JSON, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("Lead", back_populates="events")

class AnalysisHistory(Base):
    """Stores metadata about each investigation/analysis performed."""
    __tablename__ = "analysis_history"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String, nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    result_data = Column(JSON, nullable=True) # Actual analysis content (reports, ranks, etc.)
    is_saved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="analysis_history")

class AnalyticsCache(Base):
    """Cache for expensive calculation results (Cohort, Segments)."""
    __tablename__ = "analytics_cache"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    cache_key = Column(String(255), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="analytics_cache")

class RawScrapingLog(Base):
    """Stores unstructured scraping results in Supabase (replacing MongoDB)."""
    __tablename__ = "raw_scraping_logs"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    platform = Column(Enum(PlatformType), nullable=False)
    keyword = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False) # Maps to JSONB in PostgreSQL
    metadata_info = Column(JSON, nullable=True) # Renamed from 'metadata' to avoid SQL keywords
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class SyncTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"

class SyncTask(Base):
    """Tracks asynchronous synchronization tasks for robustness."""
    __tablename__ = "sync_tasks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    connection_id = Column(GUID, ForeignKey("platform_connections.id", ondelete="CASCADE"), nullable=False)
    target_date = Column(DateTime, nullable=False, index=True)
    status = Column(Enum(SyncTaskStatus), default=SyncTaskStatus.PENDING)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    attempts = Column(Integer, default=0)
    
    connection = relationship("PlatformConnection")
    validation = relationship("SyncValidation", back_populates="task", uselist=False)

class SyncValidation(Base):
    """Stores data integrity check results (Verification Layer)."""
    __tablename__ = "sync_validations"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID, ForeignKey("sync_tasks.id", ondelete="CASCADE"), nullable=False)
    is_valid = Column(Integer, default=1) # 1: valid, 0: anomaly
    checks_passed = Column(JSON, nullable=True) # {"null_check": true, "anomaly_check": false}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    task = relationship("SyncTask", back_populates="validation")


# --- AI Chat History ---

class ChatSession(Base):
    """AI 어시스턴트 대화 세션"""
    __tablename__ = "chat_sessions"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(GUID, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)  # 자동 생성 제목 (첫 메시지 기반)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """AI 어시스턴트 대화 메시지"""
    __tablename__ = "chat_messages"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)   # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    msg_type = Column(String(20), nullable=True, default="text")  # 'text' | 'markdown' | 'error'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
