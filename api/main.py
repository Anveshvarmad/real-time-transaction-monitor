from fastapi import FastAPI

from api.routes.transactions import router as transactions_router


app = FastAPI(
    title="Real-Time Fraud Detection and Transaction Monitoring API",
    description=(
        "FastAPI service for ingesting transactions, evaluating anomaly rules, "
        "and returning risk-scored fraud alerts."
    ),
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "transaction-monitoring-api",
    }


app.include_router(transactions_router)
