import random
from datetime import datetime, timedelta
from typing import Dict, List


MERCHANTS = [
    ("Amazon", "retail"),
    ("Walmart", "retail"),
    ("Target", "retail"),
    ("Starbucks", "food"),
    ("McDonalds", "food"),
    ("Shell", "fuel"),
    ("Delta", "travel"),
    ("Uber", "transport"),
    ("Netflix", "subscription"),
    ("Apple Store", "electronics"),
    ("CryptoX", "crypto"),
    ("GoldHouse", "jewelry"),
    ("QuickBet", "gambling"),
    ("MoneyFast", "money_transfer"),
]

HIGH_RISK_MERCHANTS = [
    ("CryptoX", "crypto"),
    ("GoldHouse", "jewelry"),
    ("QuickBet", "gambling"),
    ("MoneyFast", "money_transfer"),
]


def build_users(count: int = 500) -> List[Dict]:
    countries = ["US", "US", "US", "US", "CA", "GB"]

    users = []

    for index in range(1, count + 1):
        users.append({
            "user_id": f"U{index:05d}",
            "home_country": random.choice(countries),
            "device_id": f"D{index:05d}",
            "ip_address": f"10.{index // 255}.{index % 255}.{random.randint(1, 254)}",
        })

    return users


def _base_transaction(index: int, timestamp: datetime, users: List[Dict]) -> Dict:
    user = random.choice(users)
    merchant, category = random.choice(MERCHANTS)

    amount = round(random.uniform(5, 350), 2)

    return {
        "transaction_id": f"TXN{index:06d}",
        "user_id": user["user_id"],
        "amount": amount,
        "currency": "USD",
        "merchant": merchant,
        "merchant_category": category,
        "location": "Normal City",
        "country": user["home_country"],
        "user_home_country": user["home_country"],
        "timestamp": timestamp.isoformat(),
        "payment_method": random.choice(["card", "bank_transfer", "wallet"]),
        "status": random.choice(["success", "success", "success", "success", "failed"]),
        "device_id": user["device_id"],
        "ip_address": user["ip_address"],
        "channel": random.choice(["online", "pos", "mobile"]),
    }


def _make_suspicious(tx: Dict) -> Dict:
    scenario = random.choice([
        "high_amount",
        "risky_country",
        "late_night",
        "new_device",
        "wire_transfer",
        "international",
        "high_risk_merchant",
    ])

    if scenario == "high_amount":
        tx["amount"] = random.choice([6000, 9000, 12000])
        tx["channel"] = "online"

    elif scenario == "risky_country":
        tx["country"] = random.choice(["ZZ", "XY", "QX"])
        tx["location"] = "Configured Risk Zone"
        tx["currency"] = random.choice(["EUR", "GBP"])

    elif scenario == "late_night":
        original_time = datetime.fromisoformat(tx["timestamp"])
        tx["timestamp"] = original_time.replace(
            hour=random.choice([0, 1, 2, 3])
        ).isoformat()
        tx["amount"] = random.choice([2500, 4000, 8000])

    elif scenario == "new_device":
        tx["device_id"] = f"D-NEW-{random.randint(1000, 9999)}"
        tx["amount"] = random.choice([1800, 3200, 7000])

    elif scenario == "wire_transfer":
        tx["payment_method"] = "wire"
        tx["amount"] = random.choice([2500, 5000, 10000])

    elif scenario == "international":
        tx["country"] = random.choice(["DE", "SG", "AE", "IN"])
        tx["amount"] = random.choice([2200, 4500, 7500])

    elif scenario == "high_risk_merchant":
        merchant, category = random.choice(HIGH_RISK_MERCHANTS)
        tx["merchant"] = merchant
        tx["merchant_category"] = category
        tx["amount"] = random.choice([1200, 3600, 8000])

    return tx


def _make_velocity_burst(
    index: int,
    timestamp: datetime,
    users: List[Dict],
) -> List[Dict]:
    user = random.choice(users)
    merchant, category = random.choice(MERCHANTS)
    burst_amount = random.choice([99.99, 250.00, 1000.00])

    rows = []

    for burst_index in range(6):
        rows.append({
            "transaction_id": f"TXN{index + burst_index:06d}",
            "user_id": user["user_id"],
            "amount": burst_amount,
            "currency": "USD",
            "merchant": merchant,
            "merchant_category": category,
            "location": "Burst City",
            "country": user["home_country"],
            "user_home_country": user["home_country"],
            "timestamp": (
                timestamp + timedelta(seconds=burst_index * 20)
            ).isoformat(),
            "payment_method": "card",
            "status": "success",
            "device_id": user["device_id"],
            "ip_address": user["ip_address"],
            "channel": "online",
        })

    return rows


def generate_transactions(count: int = 10000, seed: int = 42) -> List[Dict]:
    random.seed(seed)

    users = build_users(count=500)
    transactions = []
    base_time = datetime.now().replace(microsecond=0) - timedelta(days=1)
    index = 1

    while len(transactions) < count:
        current_time = base_time + timedelta(seconds=index * random.randint(8, 30))

        if random.random() < 0.01 and len(transactions) + 6 < count:
            burst = _make_velocity_burst(index, current_time, users)
            transactions.extend(burst)
            index += len(burst)
            continue

        tx = _base_transaction(index, current_time, users)

        if random.random() < 0.08:
            tx = _make_suspicious(tx)

        transactions.append(tx)
        index += 1

    return transactions[:count]