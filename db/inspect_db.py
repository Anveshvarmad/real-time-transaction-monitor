from sqlalchemy import func, select

from db.models import AlertRecord, RuleMatchRecord, TransactionRecord
from db.session import SessionLocal, initialize_database


def main() -> None:
    initialize_database()

    session = SessionLocal()

    try:
        transaction_count = session.scalar(
            select(func.count()).select_from(TransactionRecord)
        )
        alert_count = session.scalar(
            select(func.count()).select_from(AlertRecord)
        )
        rule_match_count = session.scalar(
            select(func.count()).select_from(RuleMatchRecord)
        )

        print("Database summary")
        print(f"Transactions: {transaction_count}")
        print(f"Alerts: {alert_count}")
        print(f"Rule matches: {rule_match_count}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
