from datetime import timedelta
from typing import List, Set

from app.models import RuleResult, Transaction


CONFIGURED_RISK_COUNTRIES = {"ZZ", "XY", "QX"}
HIGH_RISK_MERCHANT_CATEGORIES = {
    "crypto",
    "gambling",
    "jewelry",
    "electronics",
    "money_transfer",
}


def recent_transactions(
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


def recent_user_transactions(
    history: List[Transaction],
    tx: Transaction,
    minutes: int,
) -> List[Transaction]:
    return [
        item
        for item in recent_transactions(history, tx, minutes)
        if item.user_id == tx.user_id
    ]


def prior_user_transactions(
    history: List[Transaction],
    tx: Transaction,
) -> List[Transaction]:
    return [item for item in history if item.user_id == tx.user_id]


def distinct_users(items: List[Transaction]) -> Set[str]:
    return {item.user_id for item in items}


def distinct_countries(items: List[Transaction]) -> Set[str]:
    return {item.country for item in items}


def evaluate_rules(
    tx: Transaction,
    history: List[Transaction],
) -> List[RuleResult]:
    matched = []

    user_history = prior_user_transactions(history, tx)
    user_last_5_min = recent_user_transactions(history, tx, 5)
    user_last_60_min = recent_user_transactions(history, tx, 60)
    user_last_24h = recent_user_transactions(history, tx, 1440)

    all_last_10_min = recent_transactions(history, tx, 10)
    all_last_24h = recent_transactions(history, tx, 1440)

    hour = tx.timestamp.hour

    if tx.amount > 5000:
        matched.append(RuleResult(
            "HIGH_AMOUNT",
            "Transaction amount is above 5,000.",
            30,
            "amount",
        ))

    if tx.amount > 10000:
        matched.append(RuleResult(
            "VERY_HIGH_AMOUNT",
            "Transaction amount is above 10,000.",
            45,
            "amount",
        ))

    if tx.amount < 1:
        matched.append(RuleResult(
            "MICRO_TRANSACTION",
            "Transaction amount is unusually small.",
            10,
            "amount",
        ))

    if tx.amount >= 1000 and tx.amount % 1000 == 0:
        matched.append(RuleResult(
            "ROUND_AMOUNT",
            "Large round amount transaction detected.",
            10,
            "amount",
        ))

    if len(user_last_5_min) >= 5:
        matched.append(RuleResult(
            "VELOCITY_5_MIN",
            "User made 5 or more transactions within 5 minutes.",
            35,
            "velocity",
        ))

    if len(user_last_60_min) >= 10:
        matched.append(RuleResult(
            "VELOCITY_1_HOUR",
            "User made 10 or more transactions within 1 hour.",
            30,
            "velocity",
        ))

    if tx.country in CONFIGURED_RISK_COUNTRIES:
        matched.append(RuleResult(
            "CONFIGURED_RISK_COUNTRY",
            "Transaction country is present in configured risk country list.",
            35,
            "location",
        ))

    if any(item.country != tx.country for item in user_last_60_min):
        matched.append(RuleResult(
            "LOCATION_CHANGE_1_HOUR",
            "User changed transaction country within 1 hour.",
            30,
            "location",
        ))

    if hour < 5 or hour >= 23:
        matched.append(RuleResult(
            "ODD_HOUR_TRANSACTION",
            "Transaction happened during unusual hours.",
            15,
            "time",
        ))

    if tx.merchant_category in HIGH_RISK_MERCHANT_CATEGORIES:
        matched.append(RuleResult(
            "HIGH_RISK_MERCHANT_CATEGORY",
            "Merchant category is configured as high risk.",
            25,
            "merchant",
        ))

    previous_merchants = {item.merchant for item in user_history}
    if len(user_history) >= 3 and tx.merchant not in previous_merchants:
        matched.append(RuleResult(
            "NEW_MERCHANT_FOR_USER",
            "User is transacting with a new merchant after previous activity.",
            15,
            "merchant",
        ))

    previous_devices = {item.device_id for item in user_history}
    if len(user_history) >= 3 and tx.device_id not in previous_devices:
        matched.append(RuleResult(
            "NEW_DEVICE_FOR_USER",
            "User is using a new device after previous activity.",
            25,
            "device",
        ))

    same_device_tx = [
        item for item in all_last_24h
        if item.device_id == tx.device_id
    ]
    if len(distinct_users(same_device_tx)) >= 3:
        matched.append(RuleResult(
            "MANY_USERS_SAME_DEVICE",
            "Multiple users used the same device within 24 hours.",
            35,
            "device",
        ))

    same_ip_tx = [
        item for item in all_last_24h
        if item.ip_address == tx.ip_address
    ]
    if len(distinct_users(same_ip_tx)) >= 3:
        matched.append(RuleResult(
            "MANY_USERS_SAME_IP",
            "Multiple users used the same IP address within 24 hours.",
            30,
            "network",
        ))

    duplicate_candidates = [
        item for item in all_last_10_min
        if item.user_id == tx.user_id
        and item.amount == tx.amount
        and item.merchant == tx.merchant
    ]
    if duplicate_candidates:
        matched.append(RuleResult(
            "DUPLICATE_TRANSACTION_PATTERN",
            "Same user, merchant, and amount repeated within 10 minutes.",
            30,
            "duplicate",
        ))

    recent_failed = [
        item for item in recent_user_transactions(history, tx, 30)
        if item.status == "failed"
    ]
    if tx.status == "success" and len(recent_failed) >= 3:
        matched.append(RuleResult(
            "FAILED_ATTEMPTS_BEFORE_SUCCESS",
            "Several failed attempts occurred before a successful transaction.",
            35,
            "behavior",
        ))

    if tx.status == "failed" and tx.amount > 3000:
        matched.append(RuleResult(
            "HIGH_AMOUNT_FAILED_TRANSACTION",
            "High-value transaction failed.",
            15,
            "behavior",
        ))

    countries_24h = distinct_countries(user_last_24h)
    countries_24h.add(tx.country)
    if len(countries_24h) >= 3:
        matched.append(RuleResult(
            "MULTIPLE_COUNTRIES_24H",
            "User transacted from 3 or more countries within 24 hours.",
            40,
            "location",
        ))

    if (hour < 5 or hour >= 23) and tx.amount > 2000:
        matched.append(RuleResult(
            "LATE_NIGHT_HIGH_AMOUNT",
            "High-value transaction occurred during unusual hours.",
            30,
            "time",
        ))

    if tx.country != tx.user_home_country:
        matched.append(RuleResult(
            "INTERNATIONAL_TRANSACTION",
            "Transaction country differs from user's home country.",
            15,
            "location",
        ))

    if tx.country != tx.user_home_country and tx.amount > 2000:
        matched.append(RuleResult(
            "INTERNATIONAL_HIGH_AMOUNT",
            "High-value international transaction detected.",
            35,
            "location",
        ))

    if tx.channel == "online" and tx.amount > 3000:
        matched.append(RuleResult(
            "CARD_NOT_PRESENT_HIGH_AMOUNT",
            "High-value online transaction detected.",
            25,
            "channel",
        ))

    if tx.payment_method == "wire" and tx.amount > 2000:
        matched.append(RuleResult(
            "WIRE_TRANSFER_HIGH_AMOUNT",
            "High-value wire transfer detected.",
            25,
            "payment",
        ))

    if tx.currency != "USD":
        matched.append(RuleResult(
            "NON_USD_TRANSACTION",
            "Transaction currency is not USD.",
            10,
            "currency",
        ))

    return matched