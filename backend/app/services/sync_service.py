from sqlalchemy.orm import Session
from app.models.models import SyncTask, SyncTaskStatus, SyncValidation, PlatformConnection, PlatformType
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def create_daily_tasks(self, connection_id: str, days: int = 1):
        """Creates SyncTask entries for the last N days for a specific connection."""
        from datetime import timedelta
        now_kst = datetime.utcnow() + timedelta(hours=9)
        today = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
        
        tasksCreated = []
        for i in range(days):
            target_date = today - timedelta(days=i)
            # Check if task already exists for this date/connection to avoid duplicates
            existing = self.db.query(SyncTask).filter(
                SyncTask.connection_id == connection_id,
                SyncTask.target_date == target_date
            ).first()
            
            if not existing or existing.status == SyncTaskStatus.FAILED:
                if existing:
                    task = existing
                    task.status = SyncTaskStatus.PENDING
                    task.attempts = 0
                else:
                    task = SyncTask(
                        id=uuid.uuid4(),
                        connection_id=connection_id,
                        target_date=target_date,
                        status=SyncTaskStatus.PENDING,
                        attempts=0
                    )
                    self.db.add(task)
                tasksCreated.append(task)
        
        self.db.commit()
        return tasksCreated

    def mark_as_running(self, task_id: str):
        task = self.db.query(SyncTask).filter(SyncTask.id == task_id).first()
        if task:
            task.status = SyncTaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            task.attempts += 1
            self.db.commit()
        return task

    def mark_as_completed(self, task_id: str, error: str = None):
        task = self.db.query(SyncTask).filter(SyncTask.id == task_id).first()
        if task:
            if error:
                task.status = SyncTaskStatus.FAILED
                task.error_message = error
            else:
                task.status = SyncTaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.db.commit()
        return task

class VerificationService:
    """Implements the Verification Layer to ensure data integrity after sync."""
    def __init__(self, db: Session):
        self.db = db

    def validate_sync_results(self, task_id: str):
        """Performs anomaly detection and null checks on reconciled data."""
        task = self.db.query(SyncTask).filter(SyncTask.id == task_id).first()
        if not task: return None
        
        from app.models.models import MetricsDaily, Campaign
        # Fetch metrics generated/updated for this date/connection
        metrics = self.db.query(MetricsDaily).join(Campaign).filter(
            Campaign.connection_id == task.connection_id,
            MetricsDaily.date == task.target_date,
            MetricsDaily.source == 'RECONCILED'
        ).all()
        
        checks_passed = {
            "not_empty": len(metrics) > 0,
            "no_negative_spend": all(m.spend >= 0 for m in metrics),
            "realistic_ctr": all((m.clicks / m.impressions < 0.5) if m.impressions > 0 else True for m in metrics)
        }
        
        is_valid = all(checks_passed.values())
        
        validation = self.db.query(SyncValidation).filter(SyncValidation.task_id == task_id).first()
        if not validation:
            validation = SyncValidation(id=uuid.uuid4(), task_id=task_id)
            self.db.add(validation)
            
        validation.is_valid = 1 if is_valid else 0
        validation.checks_passed = checks_passed
        validation.notes = f"Validated {len(metrics)} campaigns." if is_valid else "Anomaly detected in metrics."
        
        self.db.commit()
        return validation
