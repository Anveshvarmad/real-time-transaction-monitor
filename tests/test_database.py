from datetime import datetime

from app.models import Transaction
from db.models import TransactionRecord
from db.repository import save_transaction_result
from db.session import SessionLocal, initialize_database


def test_save_transaction_result_without_alert():
    initialize_database()

    transaction = Transaction(
        transaction_id="TXN_DB_TEST_001",
        user_id="U_DB_TEST",
        amount=125.50,
        currency="USD",
        merchant="Walmart",
        merchant_category="retail",
        location="New York",
        country="US",
        user_home_country="US",
        timestamp=datetime.now(),
        payment_method="card",
        status="success",
        device_id="D_DB_TEST",
        ip_address="127.0.0.10",
        channel="pos",
    )

    save_transaction_result(transaction, None)

    session = SessionLocal()

    try:
        saved = (
            session.query(TransactionRecord)
            .filter(TransactionRecord.transaction_id == "TXN_DB_TEST_001")
            .first()
        )

        assert saved is not None
        assert saved.user_id == "U_DB_TEST"
        assert float(saved.amount) == 125.50

    finally:
        session.close()
