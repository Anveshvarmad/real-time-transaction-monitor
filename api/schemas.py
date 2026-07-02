from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., min_length=3)
    user_id: str = Field(..., min_length=2)
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    merchant: str
    merchant_category: str
    location: str
    country: str
    user_home_country: str
    timestamp: datetime
    payment_method: str
    status: str
    device_id: str
    ip_address: str
    channel: str


class RuleMatchResponse(BaseModel):
    rule_code: str
    description: str
    risk_points: int
    category: str


class AlertResponse(BaseModel):
    transaction_id: str
    user_id: str
    risk_score: int
    alert_category: str
    matched_rules: List[RuleMatchResponse]


class TransactionIngestionResponse(BaseModel):
    transaction_id: str
    status: str
    alert_generated: bool
    risk_score: int
    alert_category: str
    alert: Optional[AlertResponse]


class BulkTransactionRequest(BaseModel):
    transactions: List[TransactionRequest]


class BulkTransactionResponse(BaseModel):
    total_received: int
    total_alerts: int
    results: List[TransactionIngestionResponse]


class EngineSummaryResponse(BaseModel):
    total_transactions_processed: int
    total_alerts_generated: int
    alert_rate_percent: float
    alert_categories: dict
    top_triggered_rules: dict
