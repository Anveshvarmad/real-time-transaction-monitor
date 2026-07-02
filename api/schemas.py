from datetime import datetime
from typing import List

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


class TransactionQueuedResponse(BaseModel):
    transaction_id: str
    status: str
    queued: bool
    queue_name: str
    queue_depth: int


class BulkTransactionRequest(BaseModel):
    transactions: List[TransactionRequest]


class BulkTransactionQueuedResponse(BaseModel):
    total_received: int
    total_queued: int
    queue_name: str
    queue_depth: int
    results: List[TransactionQueuedResponse]


class QueueSummaryResponse(BaseModel):
    queue_name: str
    queue_backend: str
    queue_depth: int
