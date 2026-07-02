import math
from datetime import timedelta
from typing import List

from app.models import Transaction
from app.rule_config import load_rule_config


FEATURE_NAMES = [
    "amount",
    "log_amount",
    "is_international",
    "is_non_usd",
    "is_high_risk_merchant",
    "is_online",
    "is_wire",
    "is_failed",
    "hour_sin",
    "hour_cos",
    "user_tx_count_5m",
    "user_tx_count_1h",
    "user_distinct_countries_24h",
    "same_device_user_count_24h",
    "same_ip_user_count_24h",
]


def _recent_transactions(
    history: List[Transaction],
    tx: Transaction,
    minutes: int,
) -> List[Transaction]:
    start_time = tx.timestamp - timedelta(minutes=minutes)

    return [
        item
        for item in history
        if start_time <= item.timestamp <= tx.timestamp
    ]


def _recent_user_transactions(
    history: List[Transaction],
    tx: Transaction,
    minutes: int,
) -> List[Transaction]:
    return [
        item
        for item in _recent_transactions(history, tx, minutes)
        if item.user_id == tx.user_id
    ]


def extract_features(
    tx: Transaction,
    history: List[Transaction],
) -> List[float]:
    config = load_rule_config()

    high_risk_categories = set(
        config.get_setting("high_risk_merchant_categories", [])
    )

    user_last_5m = _recent_user_transactions(history, tx, 5)
    user_last_1h = _recent_user_transactions(history, tx, 60)
    user_last_24h = _recent_user_transactions(history, tx, 1440)

    all_last_24h = _recent_transactions(history, tx, 1440)

    same_device_users = {
        item.user_id
        for item in all_last_24h
        if item.device_id == tx.device_id
    }

    same_ip_users = {
        item.user_id
        for item in all_last_24h
        if item.ip_address == tx.ip_address
    }

    user_countries_24h = {
        item.country
        for item in user_last_24h
    }
    user_countries_24h.add(tx.country)

    hour_angle = 2 * math.pi * tx.timestamp.hour / 24

    return [
        float(tx.amount),
        math.log1p(float(tx.amount)),
        1.0 if tx.country != tx.user_home_country else 0.0,
        1.0 if tx.currency != "USD" else 0.0,
        1.0 if tx.merchant_category in high_risk_categories else 0.0,
        1.0 if tx.channel == "online" else 0.0,
        1.0 if tx.payment_method == "wire" else 0.0,
        1.0 if tx.status == "failed" else 0.0,
        math.sin(hour_angle),
        math.cos(hour_angle),
        float(len(user_last_5m)),
        float(len(user_last_1h)),
        float(len(user_countries_24h)),
        float(len(same_device_users)),
        float(len(same_ip_users)),
    ]
