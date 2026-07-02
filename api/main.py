from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.routes.transactions import router as transactions_router


app = FastAPI(
    title="Real-Time Fraud Detection and Transaction Monitoring API",
    description=(
        "FastAPI service for ingesting transactions, queueing events, "
        "and supporting real-time fraud monitoring workflows."
    ),
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "transaction-monitoring-api",
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(transactions_router)
