import time
from pathlib import Path

from app.engine import MonitoringEngine
from app.models import Transaction
from app.storage import append_jsonl, write_json
from app.transaction_queue import QUEUE_NAME, dequeue_transaction, get_backend_name
from db.repository import save_transaction_result
from db.session import DATABASE_URL, initialize_database


OUTPUT_DIR = Path("output")
TRANSACTIONS_FILE = OUTPUT_DIR / "transactions.jsonl"
ALERTS_FILE = OUTPUT_DIR / "alerts.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "summary.json"


def run_worker() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()

    engine = MonitoringEngine()

    print("Transaction worker started.")
    print(f"Queue backend: {get_backend_name()}")
    print(f"Listening on queue: {QUEUE_NAME}")
    print(f"Database URL: {DATABASE_URL}")

    while True:
        try:
            payload = dequeue_transaction(timeout=5)

            if payload is None:
                print("Waiting for transactions...")
                continue

            transaction = Transaction.from_dict(payload)
            alert = engine.process_transaction(transaction)

            save_transaction_result(transaction, alert)

            append_jsonl(
                str(TRANSACTIONS_FILE),
                transaction.to_dict(),
            )

            if alert is not None:
                append_jsonl(
                    str(ALERTS_FILE),
                    alert.to_dict(),
                )

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

        except KeyboardInterrupt:
            print("Worker stopped.")
            break

        except Exception as error:
            print(f"Worker error: {error}")
            time.sleep(2)


if __name__ == "__main__":
    run_worker()
