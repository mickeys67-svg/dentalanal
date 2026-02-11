from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Settlement, SettlementDetail, MetricsDaily, Campaign, PlatformConnection, Client, SettlementStatus
from app.schemas.settlement import SettlementCreate, SettlementUpdate
from datetime import datetime
import uuid

class SettlementService:
    def __init__(self, db: Session):
        self.db = db

    def generate_monthly_settlement(self, client_id: str, year: int, month: int):
        """
        Aggregate MetricsDaily for the given client and month and create a Settlement.
        """
        period = f"{year}-{month:02d}"
        
        # Check if settlement already exists for this period
        existing = self.db.query(Settlement).filter(
            Settlement.client_id == client_id,
            Settlement.period == period
        ).first()
        
        if existing:
            return existing

        # Fetch aggregated metrics per platform/campaign
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Aggregate by platform and campaign
        metrics_query = self.db.query(
            PlatformConnection.platform,
            Campaign.name.label("campaign_name"),
            func.sum(MetricsDaily.spend).label("total_spend")
        ).join(Campaign, Campaign.id == MetricsDaily.campaign_id)\
         .join(PlatformConnection, PlatformConnection.id == Campaign.connection_id)\
         .filter(
             PlatformConnection.client_id == client_id,
             MetricsDaily.date >= start_date,
             MetricsDaily.date < end_date
         ).group_by(PlatformConnection.platform, Campaign.name).all()

        if not metrics_query:
            return None

        total_spend = sum(m.total_spend for m in metrics_query)
        # Default fee rate 15% - In real app, this might come from Client model or a contract table
        fee_rate = 0.15 
        total_fee = total_spend * fee_rate
        total_tax = total_fee * 0.1 # 10% VAT on fee
        total_amount = total_fee + total_tax # Amount to be invoiced by agency (some models include spend, some just fee)
        # Assuming agency invoices just the FEE + TAX if client pays ad platform directly. 
        # Or Total = Spend + Fee + Tax if agency pays on behalf. 
        # Let's assume agency invoices Fee + Tax.

        new_settlement = Settlement(
            id=uuid.uuid4(),
            client_id=client_id,
            period=period,
            total_spend=total_spend,
            fee_amount=total_fee,
            tax_amount=total_tax,
            total_amount=total_amount,
            status=SettlementStatus.PENDING,
            due_date=datetime(year, month + 1, 10) # Default due date 10th of next month
        )
        self.db.add(new_settlement)
        self.db.flush()

        for m in metrics_query:
            detail = SettlementDetail(
                id=uuid.uuid4(),
                settlement_id=new_settlement.id,
                platform=m.platform,
                campaign_name=m.campaign_name,
                spend=m.total_spend,
                fee_rate=fee_rate,
                fee_amount=m.total_spend * fee_rate
            )
            self.db.add(detail)

        self.db.commit()
        self.db.refresh(new_settlement)
        return new_settlement

    def get_client_settlements(self, client_id: str):
        return self.db.query(Settlement).filter(Settlement.client_id == client_id).order_by(Settlement.period.desc()).all()

    def update_settlement_status(self, settlement_id: str, status: SettlementStatus, notes: str = None):
        settlement = self.db.query(Settlement).filter(Settlement.id == settlement_id).first()
        if not settlement:
            return None
        
        settlement.status = status
        if status == SettlementStatus.PAID:
            settlement.paid_at = datetime.now()
        if notes:
            settlement.notes = notes
            
        self.db.commit()
        self.db.refresh(settlement)
        return settlement
