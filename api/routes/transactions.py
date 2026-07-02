from typing import List

from fastapi import APIRouter

from api.schemas import (
    BulkTransactionQueuedResponse,
    BulkTransactionRequest,
    QueueSummaryResponse,
    TransactionQueuedResponse,
    TransactionRequest,
)
from app.metrics import (
    QUEUE_DEPTH,
    TRANSACTIONS_INGESTED_TOTAL,
    TRANSACTIONS_QUEUED_TOTAL,
)
from app.transaction_queue import (
    QUEUE_NAME,
    enqueue_transaction,
    get_backend_name,
    get_queue_depth,
)


router = APIRouter(prefix="/transactions", tags=["transactions"])


def queue_single_transaction(
    request: TransactionRequest,
    endpoint: str,
) -> TransactionQueuedResponse:
    payload = request.model_dump(mode="json")
    queue_depth = enqueue_transaction(payload)

    TRANSACTIONS_INGESTED_TOTAL.labels(endpoint=endpoint).inc()
    TRANSACTIONS_QUEUED_TOTAL.labels(queue_name=QUEUE_NAME).inc()
    QUEUE_DEPTH.labels(queue_name=QUEUE_NAME).set(queue_depth)

    return TransactionQueuedResponse(
        transaction_id=request.transaction_id,
        status="queued",
        queued=True,
        queue_name=QUEUE_NAME,
        queue_depth=queue_depth,
    )


@router.post("", response_model=TransactionQueuedResponse)
def ingest_transaction(
    request: TransactionRequest,
) -> TransactionQueuedResponse:
    return queue_single_transaction(request, endpoint="single")


@router.post("/bulk", response_model=BulkTransactionQueuedResponse)
def ingest_bulk_transactions(
    request: BulkTransactionRequest,
) -> BulkTransactionQueuedResponse:
    results: List[TransactionQueuedResponse] = []

    for transaction in request.transactions:
        results.append(queue_single_transaction(transaction, endpoint="bulk"))

    queue_depth = get_queue_depth()
    QUEUE_DEPTH.labels(queue_name=QUEUE_NAME).set(queue_depth)

    return BulkTransactionQueuedResponse(
        total_received=len(request.transactions),
        total_queued=len(results),
        queue_name=QUEUE_NAME,
        queue_depth=queue_depth,
        results=results,
    )


@router.get("/queue", response_model=QueueSummaryResponse)
def get_queue_summary() -> QueueSummaryResponse:
    queue_depth = get_queue_depth()
    QUEUE_DEPTH.labels(queue_name=QUEUE_NAME).set(queue_depth)

    return QueueSummaryResponse(
        queue_name=QUEUE_NAME,
        queue_backend=get_backend_name(),
        queue_depth=queue_depth,
    )
