from typing import Optional

from sqlalchemy.orm import Session

from app.models import Alert, Transaction
from db.models import AlertRecord, RuleMatchRecord, TransactionRecord
from db.session import SessionLocal


def save_transaction_result(
    transaction: Transaction,
    alert: Optional[Alert],
) -> None:
    session: Session = SessionLocal()

    try:
        existing_transaction = (
            session.query(TransactionRecord)
            .filter(TransactionRecord.transaction_id == transaction.transaction_id)
            .first()
        )

        if existing_transaction is None:
            transaction_record = TransactionRecord(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                amount=transaction.amount,
                currency=transaction.currency,
                merchant=transaction.merchant,
                merchant_category=transaction.merchant_category,
                location=transaction.location,
                country=transaction.country,
                user_home_country=transaction.user_home_country,
                timestamp=transaction.timestamp,
                payment_method=transaction.payment_method,
                status=transaction.status,
                device_id=transaction.device_id,
                ip_address=transaction.ip_address,
                channel=transaction.channel,
            )

            session.add(transaction_record)
            session.flush()

        if alert is not None:
            existing_alert = (
                session.query(AlertRecord)
                .filter(AlertRecord.transaction_id == alert.transaction_id)
                .first()
            )

            if existing_alert is None:
                alert_record = AlertRecord(
                    transaction_id=alert.transaction_id,
                    user_id=alert.user_id,
                    risk_score=alert.risk_score,
                    alert_category=alert.alert_category,
                )

                session.add(alert_record)
                session.flush()

                for rule in alert.matched_rules:
                    rule_record = RuleMatchRecord(
                        alert_id=alert_record.id,
                        rule_code=rule.rule_code,
                        description=rule.description,
                        risk_points=rule.risk_points,
                        category=rule.category,
                    )
                    session.add(rule_record)

        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
