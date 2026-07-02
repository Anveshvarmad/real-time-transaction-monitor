from dataclasses import asdict
from typing import List

from fastapi import APIRouter

from api.schemas import (
    AlertResponse,
    BulkTransactionRequest,
    BulkTransactionResponse,
    EngineSummaryResponse,
    RuleMatchResponse,
    TransactionIngestionResponse,
    TransactionRequest,
)
from app.engine import MonitoringEngine
from app.models import Transaction


router = APIRouter(prefix="/transactions", tags=["transactions"])

engine = MonitoringEngine()


def convert_request_to_transaction(request: TransactionRequest) -> Transaction:
    payload = request.model_dump()
    return Transaction(**payload)


def convert_alert_response(alert) -> AlertResponse:
    return AlertResponse(
        transaction_id=alert.transaction_id,
        user_id=alert.user_id,
        risk_score=alert.risk_score,
        alert_category=alert.alert_category,
        matched_rules=[
            RuleMatchResponse(**asdict(rule))
            for rule in alert.matched_rules
        ],
    )


def process_single_transaction(
    request: TransactionRequest,
) -> TransactionIngestionResponse:
    transaction = convert_request_to_transaction(request)
    alert = engine.process_transaction(transaction)

    if alert is None:
        return TransactionIngestionResponse(
            transaction_id=transaction.transaction_id,
            status="processed",
            alert_generated=False,
            risk_score=0,
            alert_category="LOW_RISK",
            alert=None,
        )

    alert_response = convert_alert_response(alert)

    return TransactionIngestionResponse(
        transaction_id=transaction.transaction_id,
        status="processed",
        alert_generated=True,
        risk_score=alert.risk_score,
        alert_category=alert.alert_category,
        alert=alert_response,
    )


@router.post("", response_model=TransactionIngestionResponse)
def ingest_transaction(
    request: TransactionRequest,
) -> TransactionIngestionResponse:
    return process_single_transaction(request)


@router.post("/bulk", response_model=BulkTransactionResponse)
def ingest_bulk_transactions(
    request: BulkTransactionRequest,
) -> BulkTransactionResponse:
    results: List[TransactionIngestionResponse] = []

    for transaction in request.transactions:
        results.append(process_single_transaction(transaction))

    total_alerts = sum(1 for result in results if result.alert_generated)

    return BulkTransactionResponse(
        total_received=len(request.transactions),
        total_alerts=total_alerts,
        results=results,
    )


@router.get("/summary", response_model=EngineSummaryResponse)
def get_engine_summary() -> EngineSummaryResponse:
    return EngineSummaryResponse(**engine.summary())
