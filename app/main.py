import argparse
from pathlib import Path

from app.engine import MonitoringEngine
from app.generator import generate_transactions
from app.models import Transaction
from app.storage import write_json, write_jsonl


def run(count: int, output: str, seed: int) -> None:
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_transactions = generate_transactions(count=count, seed=seed)

    engine = MonitoringEngine()
    alerts = []

    for raw_tx in raw_transactions:
        tx = Transaction.from_dict(raw_tx)
        alert = engine.process_transaction(tx)

        if alert:
            alerts.append(alert.to_dict())

    summary = engine.summary()

    write_jsonl(
        str(output_dir / "transactions.jsonl"),
        raw_transactions,
    )
    write_jsonl(
        str(output_dir / "alerts.jsonl"),
        alerts,
    )
    write_json(
        str(output_dir / "summary.json"),
        summary,
    )

    print("Transaction monitoring completed.")
    print(f"Transactions processed: {summary['total_transactions_processed']}")
    print(f"Alerts generated: {summary['total_alerts_generated']}")
    print(f"Alert rate: {summary['alert_rate_percent']}%")
    print(f"Output folder: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-Time Transaction Monitoring System"
    )
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--output", type=str, default="output")
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    run(
        count=args.count,
        output=args.output,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()