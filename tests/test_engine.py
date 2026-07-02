from datetime import datetime, timedelta

from app.engine import MonitoringEngine
from app.models import Transaction


def make_tx(**overrides):
    base = {
        "transaction_id": "TXN_TEST_001",
        "user_id": "U_TEST",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "merchant_category": "retail",
        "location": "Test City",
        "country": "US",
        "user_home_country": "US",
        "timestamp": datetime.now(),
        "payment_method": "card",
        "status": "success",
        "device_id": "D_TEST",
        "ip_address": "127.0.0.1",
        "channel": "online",
    }

    base.update(overrides)
    return Transaction(**base)


def test_high_amount_generates_alert():
    engine = MonitoringEngine()

    tx = make_tx(
        transaction_id="TXN_HIGH_AMOUNT",
        amount=7500,
    )

    alert = engine.process_transaction(tx)

    assert alert is not None
    assert alert.risk_score >= 30
    assert "HIGH_AMOUNT" in [rule.rule_code for rule in alert.matched_rules]


def test_duplicate_transaction_pattern_generates_alert():
    engine = MonitoringEngine()
    timestamp = datetime.now()

    first_tx = make_tx(
        transaction_id="TXN_DUP_001",
        amount=500,
        merchant="Walmart",
        timestamp=timestamp,
    )

    second_tx = make_tx(
        transaction_id="TXN_DUP_002",
        amount=500,
        merchant="Walmart",
        timestamp=timestamp + timedelta(minutes=2),
    )

    engine.process_transaction(first_tx)
    alert = engine.process_transaction(second_tx)

    assert alert is not None
    assert "DUPLICATE_TRANSACTION_PATTERN" in [
        rule.rule_code for rule in alert.matched_rules
    ]


def test_normal_transaction_does_not_generate_alert():
    engine = MonitoringEngine()

    tx = make_tx(
        transaction_id="TXN_NORMAL",
        amount=45.25,
        merchant="Walmart",
        merchant_category="retail",
    )

    alert = engine.process_transaction(tx)

    assert alert is None
