import time
from pathlib import Path

from app.engine import MonitoringEngine
from app.models import Transaction
from app.transaction_queue import QUEUE_NAME, dequeue_transaction, get_backend_name
from app.storage import append_jsonl, write_json


OUTPUT_DIR = Path("output")
TRANSACTIONS_FILE = OUTPUT_DIR / "transactions.jsonl"
ALERTS_FILE = OUTPUT_DIR / "alerts.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "summary.json"


def run_worker() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = MonitoringEngine()

    print("Transaction worker started.")
    print(f"Queue backend: {get_backend_name()}")
    print(f"Listening on queue: {QUEUE_NAME}")

    while True:
        try:
            payload = dequeue_transaction(timeout=5)

            if payload is None:
                print("Waiting for transactions...")
                continue

            transaction = Transaction.from_dict(payload)
            alert = engine.process_transaction(transaction)

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
