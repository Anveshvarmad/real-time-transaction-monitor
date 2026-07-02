from datetime import datetime, timedelta

from app.engine import MonitoringEngine
from app.ml_features import FEATURE_NAMES, extract_features
from app.models import Transaction


def make_tx(index: int, amount: float = 50.0) -> Transaction:
    timestamp = datetime.now() + timedelta(seconds=index)

    return Transaction(
        transaction_id=f"TXN_ML_{index:04d}",
        user_id=f"U_ML_{index % 10}",
        amount=amount,
        currency="USD",
        merchant="Walmart",
        merchant_category="retail",
        location="New York",
        country="US",
        user_home_country="US",
        timestamp=timestamp,
        payment_method="card",
        status="success",
        device_id=f"D_ML_{index % 10}",
        ip_address=f"127.0.0.{index % 10}",
        channel="pos",
    )


def test_feature_extractor_returns_expected_length():
    tx = make_tx(1)

    features = extract_features(tx, [])

    assert len(features) == len(FEATURE_NAMES)


def test_monitoring_engine_trains_ml_after_warmup():
    engine = MonitoringEngine(enable_ml=True)

    for index in range(100):
        tx = make_tx(index, amount=50 + (index % 5))
        engine.process_transaction(tx)

    assert engine.ml_scorer is not None
    assert engine.ml_scorer.is_trained is True
