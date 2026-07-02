from datetime import timedelta
from typing import List, Set

from app.models import RuleResult, Transaction
from app.rule_config import load_rule_config


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
    return [
        item
        for item in history
        if item.user_id == tx.user_id
    ]


def distinct_users(items: List[Transaction]) -> Set[str]:
    return {item.user_id for item in items}


def distinct_countries(items: List[Transaction]) -> Set[str]:
    return {item.country for item in items}


def is_odd_hour(hour: int, start_hour: int, end_hour: int) -> bool:
    if start_hour > end_hour:
        return hour >= start_hour or hour < end_hour

    return start_hour <= hour < end_hour


def add_rule(
    matched: List[RuleResult],
    rule_code: str,
) -> None:
    config = load_rule_config()

    if config.is_enabled(rule_code):
        matched.append(config.build_result(rule_code))


def evaluate_rules(
    tx: Transaction,
    history: List[Transaction],
) -> List[RuleResult]:
    config = load_rule_config()
    matched: List[RuleResult] = []

    user_history = prior_user_transactions(history, tx)

    high_amount_threshold = config.get_param("HIGH_AMOUNT", "threshold", 5000)
    if config.is_enabled("HIGH_AMOUNT") and tx.amount > high_amount_threshold:
        add_rule(matched, "HIGH_AMOUNT")

    very_high_amount_threshold = config.get_param(
        "VERY_HIGH_AMOUNT",
        "threshold",
        10000,
    )
    if (
        config.is_enabled("VERY_HIGH_AMOUNT")
        and tx.amount > very_high_amount_threshold
    ):
        add_rule(matched, "VERY_HIGH_AMOUNT")

    micro_threshold = config.get_param("MICRO_TRANSACTION", "threshold", 1)
    if config.is_enabled("MICRO_TRANSACTION") and tx.amount < micro_threshold:
        add_rule(matched, "MICRO_TRANSACTION")

    round_min_amount = config.get_param("ROUND_AMOUNT", "min_amount", 1000)
    round_divisor = config.get_param("ROUND_AMOUNT", "divisor", 1000)
    if (
        config.is_enabled("ROUND_AMOUNT")
        and tx.amount >= round_min_amount
        and tx.amount % round_divisor == 0
    ):
        add_rule(matched, "ROUND_AMOUNT")

    velocity_5_window = config.get_param(
        "VELOCITY_5_MIN",
        "window_minutes",
        5,
    )
    velocity_5_max = config.get_param(
        "VELOCITY_5_MIN",
        "max_transactions",
        5,
    )
    user_last_5_min = recent_user_transactions(
        history,
        tx,
        velocity_5_window,
    )

    if (
        config.is_enabled("VELOCITY_5_MIN")
        and len(user_last_5_min) >= velocity_5_max
    ):
        add_rule(matched, "VELOCITY_5_MIN")

    velocity_1h_window = config.get_param(
        "VELOCITY_1_HOUR",
        "window_minutes",
        60,
    )
    velocity_1h_max = config.get_param(
        "VELOCITY_1_HOUR",
        "max_transactions",
        10,
    )
    user_last_60_min = recent_user_transactions(
        history,
        tx,
        velocity_1h_window,
    )

    if (
        config.is_enabled("VELOCITY_1_HOUR")
        and len(user_last_60_min) >= velocity_1h_max
    ):
        add_rule(matched, "VELOCITY_1_HOUR")

    configured_risk_countries = set(
        config.get_setting("configured_risk_countries", [])
    )

    if (
        config.is_enabled("CONFIGURED_RISK_COUNTRY")
        and tx.country in configured_risk_countries
    ):
        add_rule(matched, "CONFIGURED_RISK_COUNTRY")

    location_window = config.get_param(
        "LOCATION_CHANGE_1_HOUR",
        "window_minutes",
        60,
    )
    user_location_window = recent_user_transactions(
        history,
        tx,
        location_window,
    )

    if (
        config.is_enabled("LOCATION_CHANGE_1_HOUR")
        and any(item.country != tx.country for item in user_location_window)
    ):
        add_rule(matched, "LOCATION_CHANGE_1_HOUR")

    hour = tx.timestamp.hour

    odd_start_hour = config.get_param(
        "ODD_HOUR_TRANSACTION",
        "start_hour",
        23,
    )
    odd_end_hour = config.get_param(
        "ODD_HOUR_TRANSACTION",
        "end_hour",
        5,
    )

    if (
        config.is_enabled("ODD_HOUR_TRANSACTION")
        and is_odd_hour(hour, odd_start_hour, odd_end_hour)
    ):
        add_rule(matched, "ODD_HOUR_TRANSACTION")

    high_risk_merchant_categories = set(
        config.get_setting("high_risk_merchant_categories", [])
    )

    if (
        config.is_enabled("HIGH_RISK_MERCHANT_CATEGORY")
        and tx.merchant_category in high_risk_merchant_categories
    ):
        add_rule(matched, "HIGH_RISK_MERCHANT_CATEGORY")

    previous_merchants = {item.merchant for item in user_history}
    new_merchant_min_history = config.get_param(
        "NEW_MERCHANT_FOR_USER",
        "min_history_count",
        3,
    )

    if (
        config.is_enabled("NEW_MERCHANT_FOR_USER")
        and len(user_history) >= new_merchant_min_history
        and tx.merchant not in previous_merchants
    ):
        add_rule(matched, "NEW_MERCHANT_FOR_USER")

    previous_devices = {item.device_id for item in user_history}
    new_device_min_history = config.get_param(
        "NEW_DEVICE_FOR_USER",
        "min_history_count",
        3,
    )

    if (
        config.is_enabled("NEW_DEVICE_FOR_USER")
        and len(user_history) >= new_device_min_history
        and tx.device_id not in previous_devices
    ):
        add_rule(matched, "NEW_DEVICE_FOR_USER")

    same_device_window_minutes = config.get_param(
        "MANY_USERS_SAME_DEVICE",
        "window_minutes",
        1440,
    )
    same_device_min_users = config.get_param(
        "MANY_USERS_SAME_DEVICE",
        "min_distinct_users",
        3,
    )
    same_device_tx = [
        item
        for item in recent_transactions(history, tx, same_device_window_minutes)
        if item.device_id == tx.device_id
    ]

    if (
        config.is_enabled("MANY_USERS_SAME_DEVICE")
        and len(distinct_users(same_device_tx)) >= same_device_min_users
    ):
        add_rule(matched, "MANY_USERS_SAME_DEVICE")

    same_ip_window_minutes = config.get_param(
        "MANY_USERS_SAME_IP",
        "window_minutes",
        1440,
    )
    same_ip_min_users = config.get_param(
        "MANY_USERS_SAME_IP",
        "min_distinct_users",
        3,
    )
    same_ip_tx = [
        item
        for item in recent_transactions(history, tx, same_ip_window_minutes)
        if item.ip_address == tx.ip_address
    ]

    if (
        config.is_enabled("MANY_USERS_SAME_IP")
        and len(distinct_users(same_ip_tx)) >= same_ip_min_users
    ):
        add_rule(matched, "MANY_USERS_SAME_IP")

    duplicate_window = config.get_param(
        "DUPLICATE_TRANSACTION_PATTERN",
        "window_minutes",
        10,
    )
    duplicate_candidates = [
        item
        for item in recent_transactions(history, tx, duplicate_window)
        if item.user_id == tx.user_id
        and item.amount == tx.amount
        and item.merchant == tx.merchant
    ]

    if (
        config.is_enabled("DUPLICATE_TRANSACTION_PATTERN")
        and duplicate_candidates
    ):
        add_rule(matched, "DUPLICATE_TRANSACTION_PATTERN")

    failed_window = config.get_param(
        "FAILED_ATTEMPTS_BEFORE_SUCCESS",
        "window_minutes",
        30,
    )
    min_failed_attempts = config.get_param(
        "FAILED_ATTEMPTS_BEFORE_SUCCESS",
        "min_failed_attempts",
        3,
    )
    recent_failed = [
        item
        for item in recent_user_transactions(history, tx, failed_window)
        if item.status == "failed"
    ]

    if (
        config.is_enabled("FAILED_ATTEMPTS_BEFORE_SUCCESS")
        and tx.status == "success"
        and len(recent_failed) >= min_failed_attempts
    ):
        add_rule(matched, "FAILED_ATTEMPTS_BEFORE_SUCCESS")

    failed_amount_threshold = config.get_param(
        "HIGH_AMOUNT_FAILED_TRANSACTION",
        "threshold",
        3000,
    )

    if (
        config.is_enabled("HIGH_AMOUNT_FAILED_TRANSACTION")
        and tx.status == "failed"
        and tx.amount > failed_amount_threshold
    ):
        add_rule(matched, "HIGH_AMOUNT_FAILED_TRANSACTION")

    multi_country_window = config.get_param(
        "MULTIPLE_COUNTRIES_24H",
        "window_minutes",
        1440,
    )
    min_country_count = config.get_param(
        "MULTIPLE_COUNTRIES_24H",
        "min_country_count",
        3,
    )
    user_country_window = recent_user_transactions(
        history,
        tx,
        multi_country_window,
    )
    countries = distinct_countries(user_country_window)
    countries.add(tx.country)

    if (
        config.is_enabled("MULTIPLE_COUNTRIES_24H")
        and len(countries) >= min_country_count
    ):
        add_rule(matched, "MULTIPLE_COUNTRIES_24H")

    late_night_threshold = config.get_param(
        "LATE_NIGHT_HIGH_AMOUNT",
        "threshold",
        2000,
    )
    late_night_start = config.get_param(
        "LATE_NIGHT_HIGH_AMOUNT",
        "start_hour",
        23,
    )
    late_night_end = config.get_param(
        "LATE_NIGHT_HIGH_AMOUNT",
        "end_hour",
        5,
    )

    if (
        config.is_enabled("LATE_NIGHT_HIGH_AMOUNT")
        and is_odd_hour(hour, late_night_start, late_night_end)
        and tx.amount > late_night_threshold
    ):
        add_rule(matched, "LATE_NIGHT_HIGH_AMOUNT")

    if (
        config.is_enabled("INTERNATIONAL_TRANSACTION")
        and tx.country != tx.user_home_country
    ):
        add_rule(matched, "INTERNATIONAL_TRANSACTION")

    international_high_threshold = config.get_param(
        "INTERNATIONAL_HIGH_AMOUNT",
        "threshold",
        2000,
    )

    if (
        config.is_enabled("INTERNATIONAL_HIGH_AMOUNT")
        and tx.country != tx.user_home_country
        and tx.amount > international_high_threshold
    ):
        add_rule(matched, "INTERNATIONAL_HIGH_AMOUNT")

    card_not_present_threshold = config.get_param(
        "CARD_NOT_PRESENT_HIGH_AMOUNT",
        "threshold",
        3000,
    )
    card_not_present_channel = config.get_param(
        "CARD_NOT_PRESENT_HIGH_AMOUNT",
        "channel",
        "online",
    )

    if (
        config.is_enabled("CARD_NOT_PRESENT_HIGH_AMOUNT")
        and tx.channel == card_not_present_channel
        and tx.amount > card_not_present_threshold
    ):
        add_rule(matched, "CARD_NOT_PRESENT_HIGH_AMOUNT")

    wire_threshold = config.get_param(
        "WIRE_TRANSFER_HIGH_AMOUNT",
        "threshold",
        2000,
    )
    wire_payment_method = config.get_param(
        "WIRE_TRANSFER_HIGH_AMOUNT",
        "payment_method",
        "wire",
    )

    if (
        config.is_enabled("WIRE_TRANSFER_HIGH_AMOUNT")
        and tx.payment_method == wire_payment_method
        and tx.amount > wire_threshold
    ):
        add_rule(matched, "WIRE_TRANSFER_HIGH_AMOUNT")

    expected_currency = config.get_param(
        "NON_USD_TRANSACTION",
        "expected_currency",
        "USD",
    )

    if (
        config.is_enabled("NON_USD_TRANSACTION")
        and tx.currency != expected_currency
    ):
        add_rule(matched, "NON_USD_TRANSACTION")

    return matched