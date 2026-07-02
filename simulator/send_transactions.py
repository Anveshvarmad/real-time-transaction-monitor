import argparse
from typing import List

import httpx

from app.generator import generate_transactions


def chunk_rows(rows: List[dict], batch_size: int):
    for index in range(0, len(rows), batch_size):
        yield rows[index:index + batch_size]


def send_transactions(
    count: int,
    url: str,
    batch_size: int,
    seed: int,
) -> None:
    transactions = generate_transactions(count=count, seed=seed)

    total_sent = 0

    for batch in chunk_rows(transactions, batch_size):
        response = httpx.post(
            url,
            json={"transactions": batch},
            timeout=30,
        )
        response.raise_for_status()

        total_sent += len(batch)
        print(f"Queued {total_sent}/{count} transactions")

    print("Transaction simulation completed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send generated transactions to the FastAPI ingestion service."
    )
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000/transactions/bulk",
    )
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    send_transactions(
        count=args.count,
        url=args.url,
        batch_size=args.batch_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
