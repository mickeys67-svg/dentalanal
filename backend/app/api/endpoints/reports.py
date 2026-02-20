from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.models.models import ReportTemplate, Report, User, UserRole, Client, SystemConfig
from app.schemas.reports import (
    ReportTemplateCreate, ReportTemplateResponse,
    ReportCreate, ReportResponse
)
from app.api.endpoints.auth import get_current_user
from app.services.analysis import AnalysisService
from app.services.report_builder import ReportBuilderService
from app.services.pdf_generator import PDFGeneratorService
from app.services.email_service import EmailService
from pydantic import BaseModel, EmailStr
import datetime
import secrets
import json

router = APIRouter()

# --- Template Endpoints ---

@router.post("/templates", response_model=ReportTemplateResponse)
def create_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admin or Super Admin can create global/agency templates
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    agency_id = template_data.agency_id or current_user.agency_id
    
    new_template = ReportTemplate(
        name=template_data.name,
        description=template_data.description,
        agency_id=agency_id,
        config=template_data.config
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

@router.get("/templates", response_model=List[ReportTemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get global templates + agency-specific ones
    query = db.query(ReportTemplate).filter(
        (ReportTemplate.agency_id == None) | 
        (ReportTemplate.agency_id == current_user.agency_id)
    )
    return query.all()

@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
def update_template(
    template_id: UUID,
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permissions (only owner agency or global admin)
    if template.agency_id and template.agency_id != current_user.agency_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    template.name = template_data.name
    template.description = template_data.description
    template.config = template_data.config
    
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}")
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if template.agency_id and template.agency_id != current_user.agency_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    db.delete(template)
    db.commit()
    return {"status": "SUCCESS", "message": "Template deleted"}

# --- Helper for Background Tasks ---

from app.core.database import SessionLocal

def process_report_task(report_id: UUID):
    db = SessionLocal()
    try:
        service = ReportBuilderService(db)
        service.generate_report_data(report_id)
    except Exception as e:
        import logging
        logging.error(f"CRITICAL ERROR in process_report_task: {str(e)}")
        db.rollback()
    finally:
        db.close()

# --- Report Endpoints ---

@router.post("", response_model=ReportResponse)
def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify template and client access
    template = db.query(ReportTemplate).filter(ReportTemplate.id == report_data.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    new_report = Report(
        template_id=report_data.template_id,
        client_id=report_data.client_id,
        title=report_data.title,
        status="PENDING"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    # 2. Trigger data generation in background
    background_tasks.add_task(process_report_task, new_report.id)
    
    return new_report

@router.get("/all", response_model=List[ReportResponse])
def get_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all reports accessible to the current user's agency"""
    # Get all clients owned by current user's agency
    agency_clients = db.query(Client).filter(
        Client.agency_id == current_user.agency_id
    ).all()
    agency_client_ids = [c.id for c in agency_clients]

    # Get all reports for those clients
    reports = db.query(Report).filter(
        Report.client_id.in_(agency_client_ids)
    ).all()
    return reports

@router.get("/detail/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.post("/generate/{report_id}")
def generate_report_now(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    리포트 데이터 즉시 생성

    백그라운드 태스크 대신 즉시 생성하여 결과 반환
    """
    service = ReportBuilderService(db)

    try:
        report_data = service.generate_report_data(report_id)

        return {
            "status": "SUCCESS",
            "report_id": str(report_id),
            "data": report_data
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule")
def schedule_report(
    client_id: UUID,
    template_id: UUID,
    schedule: str,  # "weekly", "monthly", "daily"
    title_template: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    리포트 자동 생성 스케줄 등록

    Args:
        client_id: 클라이언트 ID
        template_id: 템플릿 ID
        schedule: 생성 주기 ("weekly", "monthly", "daily")
        title_template: 제목 템플릿 (예: "주간 리포트 - {date}")

    Returns:
        생성된 스케줄 정보
    """
    service = ReportBuilderService(db)

    # 다음 생성 일자 계산
    today = datetime.date.today()

    if schedule == "weekly":
        period_start = today - datetime.timedelta(days=7)
        period_end = today
    elif schedule == "monthly":
        # 지난 달 전체
        first_of_month = today.replace(day=1)
        period_end = first_of_month - datetime.timedelta(days=1)
        period_start = period_end.replace(day=1)
    elif schedule == "daily":
        period_start = today - datetime.timedelta(days=1)
        period_end = today - datetime.timedelta(days=1)
    else:
        raise HTTPException(status_code=400, detail="Invalid schedule type")

    # 제목 생성
    title = title_template.replace("{date}", str(today))

    try:
        report = service.create_report(
            client_id=client_id,
            template_id=template_id,
            title=title,
            period_start=period_start,
            period_end=period_end,
            schedule=schedule
        )

        return {
            "status": "SUCCESS",
            "report_id": str(report.id),
            "schedule": schedule,
            "next_run": str(today)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/{report_id}")
def download_report_pdf(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    리포트 PDF 다운로드

    Args:
        report_id: 리포트 ID

    Returns:
        PDF 파일 (application/pdf)
    """
    # 1. 리포트 조회
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 2. 템플릿 조회
    template = db.query(ReportTemplate).filter(ReportTemplate.id == report.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 3. 클라이언트 조회
    client = db.query(Client).filter(Client.id == report.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # 4. PDF 생성
    try:
        pdf_service = PDFGeneratorService()
        pdf_bytes = pdf_service.generate_report_pdf(
            report_data=report.data or {},
            template_config=template.config,
            client_name=client.name
        )

        # 5. Response 반환
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

class EmailReportRequest(BaseModel):
    report_id: UUID
    to_emails: list[EmailStr]
    subject: str
    summary: str

@router.post("/send-email")
def send_report_email(
    request: EmailReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    리포트 이메일 발송

    Args:
        request: 이메일 발송 요청
            - report_id: 리포트 ID
            - to_emails: 수신자 이메일 목록
            - subject: 이메일 제목
            - summary: 리포트 요약

    Returns:
        발송 결과
    """
    # 1. 리포트 조회
    report = db.query(Report).filter(Report.id == request.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 2. 템플릿 조회
    template = db.query(ReportTemplate).filter(ReportTemplate.id == report.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 3. 클라이언트 조회
    client = db.query(Client).filter(Client.id == report.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # 4. PDF 생성
    try:
        pdf_service = PDFGeneratorService()
        pdf_bytes = pdf_service.generate_report_pdf(
            report_data=report.data or {},
            template_config=template.config,
            client_name=client.name
        )

        # 5. 이메일 발송
        email_service = EmailService()
        success = email_service.send_report_email(
            to_emails=request.to_emails,
            subject=request.subject,
            report_title=report.title,
            client_name=client.name,
            summary=request.summary,
            pdf_bytes=pdf_bytes,
            pdf_filename=f"report_{report.id}.pdf"
        )

        if success:
            return {
                "status": "SUCCESS",
                "message": f"Email sent to {len(request.to_emails)} recipients"
            }
        else:
            raise HTTPException(status_code=500, detail="Email sending failed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


# ─── 클라이언트 포털 공유 ──────────────────────────────────────────────────────

@router.post("/share/{client_id}")
def create_share_token(
    client_id: UUID,
    expires_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    클라이언트 포털 공유 토큰 생성 (읽기 전용 링크)

    생성된 토큰으로 /portal/{token} 에 접근 시 로그인 없이 해당 클라이언트의
    핵심 KPI를 열람할 수 있습니다.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Verify the client belongs to the current user's agency
    if client.agency_id != current_user.agency_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)).isoformat()

    config_key = f"PORTAL_TOKEN_{token}"
    payload = json.dumps({"client_id": str(client_id), "expires_at": expires_at})

    existing = db.query(SystemConfig).filter(SystemConfig.key == config_key).first()
    if existing:
        existing.value = payload
    else:
        db.add(SystemConfig(key=config_key, value=payload, description=f"Portal share token for {client.name}"))
    db.commit()

    return {"token": token, "expires_at": expires_at, "client_name": client.name}


@router.get("/portal/{token}")
def get_portal_data(
    token: str,
    db: Session = Depends(get_db),
):
    """
    공유 토큰으로 클라이언트 포털 데이터 조회 (인증 불필요)
    """
    config_key = f"PORTAL_TOKEN_{token}"
    config = db.query(SystemConfig).filter(SystemConfig.key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="유효하지 않은 공유 링크입니다.")

    try:
        payload = json.loads(config.value)
    except Exception:
        raise HTTPException(status_code=500, detail="토큰 데이터 오류")

    expires_at = datetime.datetime.fromisoformat(payload["expires_at"])
    if datetime.datetime.utcnow() > expires_at:
        raise HTTPException(status_code=410, detail="만료된 공유 링크입니다.")

    client_id = UUID(payload["client_id"])
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="클라이언트를 찾을 수 없습니다.")

    # 최근 30일 리포트 목록
    recent_reports = db.query(Report).filter(
        Report.client_id == client_id,
        Report.status == "COMPLETED"
    ).order_by(Report.created_at.desc()).limit(5).all()

    return {
        "client": {"id": str(client.id), "name": client.name, "industry": client.industry},
        "expires_at": payload["expires_at"],
        "reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "period_start": str(r.period_start) if r.period_start else None,
                "period_end": str(r.period_end) if r.period_end else None,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "data_summary": _extract_summary(r.data),
            }
            for r in recent_reports
        ]
    }


@router.get("/{client_id}", response_model=List[ReportResponse])
def get_client_reports(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """클라이언트별 리포트 목록 조회 (와일드카드 — 반드시 모든 구체 경로 뒤에 위치)"""
    return db.query(Report).filter(Report.client_id == client_id).all()


def _extract_summary(data: Optional[dict]) -> dict:
    """리포트 data JSON에서 핵심 KPI만 추출"""
    if not data:
        return {}
    summary = {}
    for widget in data.get("widgets", []):
        wtype = widget.get("type", "")
        if wtype == "KPI_GROUP":
            summary["kpis"] = widget.get("data", [])
        elif wtype == "FUNNEL":
            summary["funnel"] = widget.get("data", [])
    return summary
