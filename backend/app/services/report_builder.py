from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.models import Report, ReportTemplate, Client, User
from typing import List, Dict, Optional
from uuid import UUID, uuid4
import datetime
import logging
import json

class ReportBuilderService:
    """
    리포트 빌더 서비스

    주요 기능:
    1. 리포트 템플릿 관리 (CRUD)
    2. 위젯 기반 리포트 생성
    3. 리포트 데이터 수집 및 렌더링
    4. 리포트 스케줄링
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def create_template(
        self,
        name: str,
        description: str,
        config: Dict,
        created_by: Optional[UUID] = None
    ) -> ReportTemplate:
        """
        리포트 템플릿 생성

        Args:
            name: 템플릿 이름
            description: 템플릿 설명
            config: 위젯 설정 (JSON)
            created_by: 생성자 ID

        Returns:
            생성된 템플릿
        """
        template = ReportTemplate(
            id=uuid4(),
            name=name,
            description=description,
            config=config,
            created_by=created_by
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        self.logger.info(f"Template created: {template.id} - {name}")
        return template

    def get_templates(
        self,
        user_id: Optional[UUID] = None,
        include_public: bool = True
    ) -> List[ReportTemplate]:
        """
        리포트 템플릿 목록 조회

        Args:
            user_id: 사용자 ID (None이면 전체)
            include_public: 공개 템플릿 포함 여부

        Returns:
            템플릿 목록
        """
        query = self.db.query(ReportTemplate)

        if user_id and not include_public:
            query = query.filter(ReportTemplate.created_by == user_id)
        elif user_id and include_public:
            query = query.filter(
                or_(
                    ReportTemplate.created_by == user_id,
                    ReportTemplate.created_by == None  # 공개 템플릿
                )
            )

        return query.order_by(ReportTemplate.created_at.desc()).all()

    def update_template(
        self,
        template_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> ReportTemplate:
        """템플릿 수정"""
        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()

        if not template:
            raise ValueError(f"Template {template_id} not found")

        if name:
            template.name = name
        if description:
            template.description = description
        if config:
            template.config = config

        self.db.commit()
        self.db.refresh(template)

        return template

    def delete_template(self, template_id: UUID) -> bool:
        """템플릿 삭제"""
        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()

        if not template:
            return False

        self.db.delete(template)
        self.db.commit()

        return True

    def create_report(
        self,
        client_id: UUID,
        template_id: UUID,
        title: str,
        period_start: datetime.date,
        period_end: datetime.date,
        schedule: Optional[str] = None
    ) -> Report:
        """
        리포트 생성

        Args:
            client_id: 클라이언트 ID
            template_id: 템플릿 ID
            title: 리포트 제목
            period_start: 분석 시작일
            period_end: 분석 종료일
            schedule: 자동 생성 스케줄 (예: "weekly", "monthly")

        Returns:
            생성된 리포트
        """
        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()

        if not template:
            raise ValueError(f"Template {template_id} not found")

        report = Report(
            id=uuid4(),
            client_id=client_id,
            template_id=template_id,
            title=title,
            period_start=period_start,
            period_end=period_end,
            status="PENDING",
            schedule=schedule
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        self.logger.info(f"Report created: {report.id} - {title}")
        return report

    def generate_report_data(
        self,
        report_id: UUID
    ) -> Dict:
        """
        리포트 데이터 생성

        템플릿의 위젯 설정에 따라 실제 데이터를 수집하고 렌더링

        Args:
            report_id: 리포트 ID

        Returns:
            생성된 리포트 데이터
        """
        report = self.db.query(Report).filter(Report.id == report_id).first()

        if not report:
            raise ValueError(f"Report {report_id} not found")

        template = report.template

        # 위젯별 데이터 생성
        widgets_data = []

        for widget in template.config.get("widgets", []):
            widget_type = widget.get("type")
            widget_data = self._generate_widget_data(
                widget_type=widget_type,
                widget_config=widget,
                client_id=report.client_id,
                period_start=report.period_start,
                period_end=report.period_end
            )

            widgets_data.append({
                "id": widget.get("id"),
                "type": widget_type,
                "title": widget.get("title"),
                "data": widget_data
            })

        report_data = {
            "title": report.title,
            "client_name": report.client.name,
            "period": f"{report.period_start} ~ {report.period_end}",
            "generated_at": datetime.datetime.now().isoformat(),
            "widgets": widgets_data
        }

        # 리포트 상태 업데이트
        report.data = report_data
        report.status = "COMPLETED"
        report.generated_at = datetime.datetime.now()

        self.db.commit()
        self.db.refresh(report)

        return report_data

    def _generate_widget_data(
        self,
        widget_type: str,
        widget_config: Dict,
        client_id: UUID,
        period_start: datetime.date,
        period_end: datetime.date
    ) -> Dict:
        """
        위젯별 데이터 생성

        지원하는 위젯 타입:
        - KPI_GROUP: 주요 지표 요약
        - FUNNEL: 전환 퍼널
        - COHORT: 코호트 분석
        - SOV: Share of Voice
        - ROI_COMPARISON: 캠페인별 ROI 비교
        - TREND_CHART: 트렌드 차트
        """
        from app.services.analysis import AnalysisService
        from app.services.roi_optimizer import ROIOptimizerService
        from app.models.models import MetricsDaily, Campaign, PlatformConnection

        analysis_service = AnalysisService(self.db)
        roi_service = ROIOptimizerService(self.db)

        if widget_type == "KPI_GROUP":
            # 주요 지표 집계
            metrics = self.db.query(
                func.sum(MetricsDaily.spend).label("total_spend"),
                func.sum(MetricsDaily.impressions).label("total_impressions"),
                func.sum(MetricsDaily.clicks).label("total_clicks"),
                func.sum(MetricsDaily.conversions).label("total_conversions")
            ).join(Campaign).join(PlatformConnection).filter(
                and_(
                    PlatformConnection.client_id == client_id,
                    MetricsDaily.date >= period_start,
                    MetricsDaily.date <= period_end,
                    MetricsDaily.source == 'RECONCILED'
                )
            ).first()

            return {
                "kpis": [
                    {"label": "총 광고비", "value": int(metrics.total_spend or 0), "unit": "원"},
                    {"label": "노출수", "value": int(metrics.total_impressions or 0), "unit": "회"},
                    {"label": "클릭수", "value": int(metrics.total_clicks or 0), "unit": "회"},
                    {"label": "전환수", "value": int(metrics.total_conversions or 0), "unit": "건"}
                ]
            }

        elif widget_type == "FUNNEL":
            # 전환 퍼널
            days = (period_end - period_start).days
            return analysis_service.get_funnel_data(
                client_id=str(client_id),
                start_date=period_start,
                end_date=period_end,
                days=days
            )

        elif widget_type == "COHORT":
            # 코호트 분석
            return {
                "cohorts": analysis_service.get_cohort_data(str(client_id))
            }

        elif widget_type == "ROI_COMPARISON":
            # 캠페인별 ROI 비교
            days = (period_end - period_start).days
            roas_data = roi_service.track_campaign_roas(
                client_id=client_id,
                days=days
            )
            return {
                "campaigns": roas_data["campaigns"][:10]  # 상위 10개만
            }

        elif widget_type == "TREND_CHART":
            # 일별 트렌드
            daily_metrics = self.db.query(
                MetricsDaily.date,
                func.sum(MetricsDaily.spend).label("spend"),
                func.sum(MetricsDaily.conversions).label("conversions")
            ).join(Campaign).join(PlatformConnection).filter(
                and_(
                    PlatformConnection.client_id == client_id,
                    MetricsDaily.date >= period_start,
                    MetricsDaily.date <= period_end,
                    MetricsDaily.source == 'RECONCILED'
                )
            ).group_by(MetricsDaily.date).order_by(MetricsDaily.date).all()

            return {
                "data": [{
                    "date": str(m.date),
                    "spend": float(m.spend or 0),
                    "conversions": int(m.conversions or 0)
                } for m in daily_metrics]
            }

        else:
            return {"error": f"Unknown widget type: {widget_type}"}

    def get_reports(
        self,
        client_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Report]:
        """리포트 목록 조회"""
        query = self.db.query(Report)

        if client_id:
            query = query.filter(Report.client_id == client_id)
        if status:
            query = query.filter(Report.status == status)

        return query.order_by(Report.created_at.desc()).limit(limit).all()

    def get_report(self, report_id: UUID) -> Optional[Report]:
        """특정 리포트 조회"""
        return self.db.query(Report).filter(Report.id == report_id).first()

    def delete_report(self, report_id: UUID) -> bool:
        """리포트 삭제"""
        report = self.db.query(Report).filter(Report.id == report_id).first()

        if not report:
            return False

        self.db.delete(report)
        self.db.commit()

        return True
