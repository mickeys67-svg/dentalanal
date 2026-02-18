"""Add all missing tables (Phase 1-4 models)

Revision ID: c3f8a912b045
Revises: aaec4a73a509
Create Date: 2026-02-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3f8a912b045'
down_revision: Union[str, None] = 'aaec4a73a509'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. New ENUM types ──────────────────────────────────────────────────────
    # PlatformType (used in multiple tables)
    platform_type = sa.Enum(
        'NAVER_VIEW', 'NAVER_PLACE', 'NAVER_AD', 'GOOGLE_ADS', 'META_ADS', 'KAKAO_AD',
        name='platformtype'
    )
    platform_type.create(op.get_bind(), checkfirst=True)

    # UserRole
    user_role = sa.Enum(
        'SUPER_ADMIN', 'ADMIN', 'EDITOR', 'VIEWER',
        name='userrole'
    )
    user_role.create(op.get_bind(), checkfirst=True)

    # SettlementStatus
    settlement_status = sa.Enum(
        'PENDING', 'ISSUED', 'PAID', 'OVERDUE', 'CANCELLED',
        name='settlementstatus'
    )
    settlement_status.create(op.get_bind(), checkfirst=True)

    # SyncTaskStatus
    sync_task_status = sa.Enum(
        'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL',
        name='synctaskstatus'
    )
    sync_task_status.create(op.get_bind(), checkfirst=True)

    # ── 2. system_configs ──────────────────────────────────────────────────────
    op.create_table(
        'system_configs',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 3. agencies ───────────────────────────────────────────────────────────
    op.create_table(
        'agencies',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('branding_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # ── 4. users ──────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'ADMIN', 'EDITOR', 'VIEWER', name='userrole', create_type=False), nullable=True),
        sa.Column('is_active', sa.Integer(), default=1),
        sa.Column('birth_date', sa.String(), nullable=True),
        sa.Column('agency_id', sa.UUID(), sa.ForeignKey('agencies.id'), nullable=True),
        sa.Index('ix_users_email', 'email'),
    )

    # ── 5. clients ────────────────────────────────────────────────────────────
    op.create_table(
        'clients',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('agency_id', sa.UUID(), sa.ForeignKey('agencies.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 6. platform_connections ───────────────────────────────────────────────
    op.create_table(
        'platform_connections',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.Enum('NAVER_VIEW', 'NAVER_PLACE', 'NAVER_AD', 'GOOGLE_ADS', 'META_ADS', 'KAKAO_AD', name='platformtype', create_type=False), nullable=False),
        sa.Column('credentials', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('access_token', sa.String(500), nullable=True),
        sa.Column('refresh_token', sa.String(500), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('account_name', sa.String(255), nullable=True),
        sa.Column('account_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Integer(), default=1),
        sa.Column('status', sa.String(), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 7. campaigns ──────────────────────────────────────────────────────────
    op.create_table(
        'campaigns',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('connection_id', sa.UUID(), sa.ForeignKey('platform_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
    )

    # ── 8. ad_groups ──────────────────────────────────────────────────────────
    op.create_table(
        'ad_groups',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('campaign_id', sa.UUID(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(), unique=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 9. ad_keywords ────────────────────────────────────────────────────────
    op.create_table(
        'ad_keywords',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('ad_group_id', sa.UUID(), sa.ForeignKey('ad_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(), unique=True, nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('bid_amt', sa.Integer(), default=0),
        sa.Column('status', sa.String(), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 10. ad_metrics_daily ──────────────────────────────────────────────────
    op.create_table(
        'ad_metrics_daily',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('date', sa.DateTime(), nullable=False, index=True),
        sa.Column('ad_group_id', sa.UUID(), sa.ForeignKey('ad_groups.id', ondelete='CASCADE'), nullable=True),
        sa.Column('keyword_id', sa.UUID(), sa.ForeignKey('ad_keywords.id', ondelete='CASCADE'), nullable=True),
        sa.Column('impressions', sa.Integer(), default=0),
        sa.Column('clicks', sa.Integer(), default=0),
        sa.Column('spend', sa.Float(), default=0.0),
        sa.Column('conversions', sa.Integer(), default=0),
        sa.Column('ctr', sa.Float(), default=0.0),
        sa.Column('cpc', sa.Float(), default=0.0),
        sa.Column('roas', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 11. metrics_daily ─────────────────────────────────────────────────────
    op.create_table(
        'metrics_daily',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('campaign_id', sa.UUID(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('spend', sa.Float(), default=0.0),
        sa.Column('impressions', sa.Integer(), default=0),
        sa.Column('clicks', sa.Integer(), default=0),
        sa.Column('conversions', sa.Integer(), default=0),
        sa.Column('revenue', sa.Float(), default=0.0),
        sa.Column('source', sa.String(), default='API'),
        sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # ── 12. Add client_id to existing keywords & daily_ranks ─────────────────
    op.add_column('keywords', sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=True))
    op.add_column('daily_ranks', sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=True))

    # ── 13. swot_analyses ─────────────────────────────────────────────────────
    op.create_table(
        'swot_analyses',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('weaknesses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('opportunities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('threats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 14. strategy_goals ────────────────────────────────────────────────────
    op.create_table(
        'strategy_goals',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('smart_s', sa.String(), nullable=True),
        sa.Column('smart_m', sa.String(), nullable=True),
        sa.Column('smart_a', sa.String(), nullable=True),
        sa.Column('smart_r', sa.String(), nullable=True),
        sa.Column('smart_t', sa.String(), nullable=True),
        sa.Column('status', sa.String(), default='IN_PROGRESS'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 15. collaborative_tasks ───────────────────────────────────────────────
    op.create_table(
        'collaborative_tasks',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('owner', sa.String(), nullable=True),
        sa.Column('deadline', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 16. task_comments ─────────────────────────────────────────────────────
    op.create_table(
        'task_comments',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('task_id', sa.UUID(), sa.ForeignKey('collaborative_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 17. approval_requests ─────────────────────────────────────────────────
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requester_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 18. notices ───────────────────────────────────────────────────────────
    op.create_table(
        'notices',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('agency_id', sa.UUID(), sa.ForeignKey('agencies.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_pinned', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 19. report_templates ──────────────────────────────────────────────────
    op.create_table(
        'report_templates',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('agency_id', sa.UUID(), sa.ForeignKey('agencies.id'), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 20. reports ───────────────────────────────────────────────────────────
    op.create_table(
        'reports',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('template_id', sa.UUID(), sa.ForeignKey('report_templates.id'), nullable=False),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 21. notifications ─────────────────────────────────────────────────────
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('link', sa.String(), nullable=True),
        sa.Column('is_read', sa.Integer(), default=0),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 22. settlements ───────────────────────────────────────────────────────
    op.create_table(
        'settlements',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('total_spend', sa.Float(), default=0.0),
        sa.Column('fee_amount', sa.Float(), default=0.0),
        sa.Column('tax_amount', sa.Float(), default=0.0),
        sa.Column('total_amount', sa.Float(), default=0.0),
        sa.Column('status', sa.Enum('PENDING', 'ISSUED', 'PAID', 'OVERDUE', 'CANCELLED', name='settlementstatus', create_type=False), default='PENDING'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 23. settlement_details ────────────────────────────────────────────────
    op.create_table(
        'settlement_details',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('settlement_id', sa.UUID(), sa.ForeignKey('settlements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.Enum('NAVER_VIEW', 'NAVER_PLACE', 'NAVER_AD', 'GOOGLE_ADS', 'META_ADS', 'KAKAO_AD', name='platformtype', create_type=False), nullable=False),
        sa.Column('campaign_name', sa.String(), nullable=True),
        sa.Column('spend', sa.Float(), default=0.0),
        sa.Column('fee_rate', sa.Float(), default=0.0),
        sa.Column('fee_amount', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 24. leads ─────────────────────────────────────────────────────────────
    op.create_table(
        'leads',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('contact', sa.String(), nullable=True),
        sa.Column('first_visit_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('cohort_month', sa.String(7), nullable=False),
        sa.Column('channel', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 25. lead_activities ───────────────────────────────────────────────────
    op.create_table(
        'lead_activities',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('lead_id', sa.UUID(), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_month', sa.String(7), nullable=False),
        sa.Column('visits', sa.Integer(), default=0),
        sa.Column('conversions', sa.Integer(), default=0),
        sa.Column('revenue', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 26. lead_profiles ─────────────────────────────────────────────────────
    op.create_table(
        'lead_profiles',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('lead_id', sa.UUID(), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('region', sa.String(50), nullable=True),
        sa.Column('user_type', sa.String(20), nullable=True),
        sa.Column('first_conversion_date', sa.DateTime(), nullable=True),
        sa.Column('last_visit_date', sa.DateTime(), nullable=True),
        sa.Column('total_visits', sa.Integer(), default=0),
        sa.Column('total_conversions', sa.Integer(), default=0),
        sa.Column('total_revenue', sa.Float(), default=0.0),
    )

    # ── 27. lead_events ───────────────────────────────────────────────────────
    op.create_table(
        'lead_events',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('lead_id', sa.UUID(), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('platform', sa.Enum('NAVER_VIEW', 'NAVER_PLACE', 'NAVER_AD', 'GOOGLE_ADS', 'META_ADS', 'KAKAO_AD', name='platformtype', create_type=False), nullable=True),
        sa.Column('segment_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 28. analysis_history ──────────────────────────────────────────────────
    op.create_table(
        'analysis_history',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('keyword', sa.String(), nullable=False),
        sa.Column('platform', sa.Enum('NAVER_VIEW', 'NAVER_PLACE', 'NAVER_AD', 'GOOGLE_ADS', 'META_ADS', 'KAKAO_AD', name='platformtype', create_type=False), nullable=False),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_saved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 29. analytics_cache ───────────────────────────────────────────────────
    op.create_table(
        'analytics_cache',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False, index=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ── 30. raw_scraping_logs ─────────────────────────────────────────────────
    op.create_table(
        'raw_scraping_logs',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('platform', sa.Enum('NAVER_VIEW', 'NAVER_PLACE', 'NAVER_AD', 'GOOGLE_ADS', 'META_ADS', 'KAKAO_AD', name='platformtype', create_type=False), nullable=False),
        sa.Column('keyword', sa.String(), nullable=False, index=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
    )

    # ── 31. sync_tasks ────────────────────────────────────────────────────────
    op.create_table(
        'sync_tasks',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('connection_id', sa.UUID(), sa.ForeignKey('platform_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_date', sa.DateTime(), nullable=False, index=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL', name='synctaskstatus', create_type=False), default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts', sa.Integer(), default=0),
    )

    # ── 32. sync_validations ──────────────────────────────────────────────────
    op.create_table(
        'sync_validations',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('task_id', sa.UUID(), sa.ForeignKey('sync_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_valid', sa.Integer(), default=1),
        sa.Column('checks_passed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('sync_validations')
    op.drop_table('sync_tasks')
    op.drop_table('raw_scraping_logs')
    op.drop_table('analytics_cache')
    op.drop_table('analysis_history')
    op.drop_table('lead_events')
    op.drop_table('lead_profiles')
    op.drop_table('lead_activities')
    op.drop_table('leads')
    op.drop_table('settlement_details')
    op.drop_table('settlements')
    op.drop_table('notifications')
    op.drop_table('reports')
    op.drop_table('report_templates')
    op.drop_table('notices')
    op.drop_table('approval_requests')
    op.drop_table('task_comments')
    op.drop_table('collaborative_tasks')
    op.drop_table('strategy_goals')
    op.drop_table('swot_analyses')
    op.drop_column('daily_ranks', 'client_id')
    op.drop_column('keywords', 'client_id')
    op.drop_table('metrics_daily')
    op.drop_table('ad_metrics_daily')
    op.drop_table('ad_keywords')
    op.drop_table('ad_groups')
    op.drop_table('campaigns')
    op.drop_table('platform_connections')
    op.drop_table('clients')
    op.drop_table('users')
    op.drop_table('agencies')
    op.drop_table('system_configs')
    sa.Enum(name='synctaskstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='settlementstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='platformtype').drop(op.get_bind(), checkfirst=True)
