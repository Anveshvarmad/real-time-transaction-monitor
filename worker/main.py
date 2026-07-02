import os
import time
from pathlib import Path

from prometheus_client import start_http_server

from app.engine import MonitoringEngine
from app.metrics import (
    ALERTS_GENERATED_TOTAL,
    ML_TRAINED_STATUS,
    QUEUE_DEPTH,
    RULE_MATCHES_TOTAL,
    TRANSACTIONS_PROCESSED_TOTAL,
    WORKER_ERRORS_TOTAL,
    WORKER_PROCESSING_LATENCY_SECONDS,
)
from app.models import Transaction
from app.storage import append_jsonl, write_json
from app.transaction_queue import (
    QUEUE_NAME,
    dequeue_transaction,
    get_backend_name,
    get_queue_depth,
)
from db.repository import save_transaction_result
from db.session import DATABASE_URL, initialize_database


OUTPUT_DIR = Path("output")
TRANSACTIONS_FILE = OUTPUT_DIR / "transactions.jsonl"
ALERTS_FILE = OUTPUT_DIR / "alerts.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "summary.json"


def run_worker() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()

    metrics_port = int(os.getenv("WORKER_METRICS_PORT", "9100"))
    start_http_server(metrics_port)

    engine = MonitoringEngine()

    print("Transaction worker started.")
    print(f"Queue backend: {get_backend_name()}")
    print(f"Listening on queue: {QUEUE_NAME}")
    print(f"Database URL: {DATABASE_URL}")
    print(f"Worker metrics exposed on port: {metrics_port}")

    while True:
        try:
            queue_depth = get_queue_depth()
            QUEUE_DEPTH.labels(queue_name=QUEUE_NAME).set(queue_depth)

            payload = dequeue_transaction(timeout=5)

            if payload is None:
                print("Waiting for transactions...")
                continue

            started_at = time.perf_counter()

            transaction = Transaction.from_dict(payload)
            alert = engine.process_transaction(transaction)

            save_transaction_result(transaction, alert)

            append_jsonl(
                str(TRANSACTIONS_FILE),
                transaction.to_dict(),
            )

            TRANSACTIONS_PROCESSED_TOTAL.inc()

            if engine.ml_scorer is not None:
                ML_TRAINED_STATUS.set(1 if engine.ml_scorer.is_trained else 0)

            if alert is not None:
                append_jsonl(
                    str(ALERTS_FILE),
                    alert.to_dict(),
                )

                ALERTS_GENERATED_TOTAL.labels(
                    alert_category=alert.alert_category
                ).inc()

                for rule in alert.matched_rules:
                    RULE_MATCHES_TOTAL.labels(
                        rule_code=rule.rule_code,
                        category=rule.category,
                    ).inc()

                print(
                    "Alert generated "
                    f"transaction_id={alert.transaction_id} "
                    f"risk_score={alert.risk_score} "
                    f"category={alert.alert_category}"
                )
            else:
                print(
                    "Transaction processed "
                    f"transaction_id={transaction.transaction_id} "
                    "risk=LOW"
                )

            write_json(
                str(SUMMARY_FILE),
                engine.summary(),
            )

            elapsed = time.perf_counter() - started_at
            WORKER_PROCESSING_LATENCY_SECONDS.observe(elapsed)

        except KeyboardInterrupt:
            print("Worker stopped.")
            break

        except Exception as error:
            WORKER_ERRORS_TOTAL.inc()
            print(f"Worker error: {error}")
            time.sleep(2)


if __name__ == "__main__":
    run_worker()
