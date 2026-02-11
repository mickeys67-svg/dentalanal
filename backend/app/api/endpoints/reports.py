from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.models.models import ReportTemplate, Report, User, UserRole
from app.schemas.reports import (
    ReportTemplateCreate, ReportTemplateResponse,
    ReportCreate, ReportResponse
)
from app.api.endpoints.auth import get_current_user
from app.services.analysis import AnalysisService # We'll extend this service for report data

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
        service = AnalysisService(db)
        service.generate_report_data(report_id)
    except Exception as e:
        import logging
        logging.error(f"CRITICAL ERROR in process_report_task: {str(e)}")
    finally:
        db.close()

# --- Report Endpoints ---

@router.post("/", response_model=ReportResponse)
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

@router.get("/{client_id}", response_model=List[ReportResponse])
def get_client_reports(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Report).filter(Report.client_id == client_id).all()
