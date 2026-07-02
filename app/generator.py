import random
from datetime import datetime, timedelta
from typing import Dict, List


MERCHANTS = [
    ("Amazon", "retail"),
    ("Walmart", "retail"),
    ("Shell", "fuel"),
    ("Delta", "travel"),
    ("Apple Store", "electronics"),
    ("CryptoX", "crypto"),
    ("GoldHouse", "jewelry"),
    ("QuickBet", "gambling"),
    ("MoneyFast", "money_transfer"),
]

USERS = [
    {
        "user_id": "U1001",
        "home_country": "US",
        "device_id": "D1001",
        "ip_address": "192.168.1.10",
    },
    {
        "user_id": "U1002",
        "home_country": "US",
        "device_id": "D1002",
        "ip_address": "192.168.1.11",
    },
    {
        "user_id": "U1003",
        "home_country": "US",
        "device_id": "D1003",
        "ip_address": "192.168.1.12",
    },
    {
        "user_id": "U1004",
        "home_country": "CA",
        "device_id": "D1004",
        "ip_address": "10.0.0.5",
    },
]


def _base_transaction(index: int, timestamp: datetime) -> Dict:
    user = random.choice(USERS)
    merchant, category = random.choice(MERCHANTS)

    amount = round(random.uniform(5, 450), 2)
    country = user["home_country"]

    return {
        "transaction_id": f"TXN{index:06d}",
        "user_id": user["user_id"],
        "amount": amount,
        "currency": "USD",
        "merchant": merchant,
        "merchant_category": category,
        "location": "Normal City",
        "country": country,
        "user_home_country": user["home_country"],
        "timestamp": timestamp.isoformat(),
        "payment_method": random.choice(["card", "bank_transfer", "wallet"]),
        "status": random.choice(["success", "success", "success", "failed"]),
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
        tx["amount"] = random.choice([6000, 9000, 12000, 15000])
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
        tx["country"] = random.choice(["GB", "DE", "SG", "AE"])
        tx["amount"] = random.choice([2200, 4500, 7500])

    elif scenario == "high_risk_merchant":
        merchant, category = random.choice([
            ("CryptoX", "crypto"),
            ("QuickBet", "gambling"),
            ("GoldHouse", "jewelry"),
            ("MoneyFast", "money_transfer"),
        ])
        tx["merchant"] = merchant
        tx["merchant_category"] = category
        tx["amount"] = random.choice([1200, 3600, 8000])

    return tx


def generate_transactions(count: int = 10000, seed: int = 42) -> List[Dict]:
    random.seed(seed)

    transactions = []
    base_time = datetime.now().replace(microsecond=0) - timedelta(days=1)
    index = 1

    while len(transactions) < count:
        current_time = base_time + timedelta(
            seconds=index * random.randint(2, 12)
        )

        if random.random() < 0.04 and len(transactions) + 6 < count:
            user = random.choice(USERS)
            merchant, category = random.choice(MERCHANTS)
            burst_amount = random.choice([99.99, 250.00, 1000.00])

            for burst_index in range(6):
                tx = {
                    "transaction_id": f"TXN{index:06d}",
                    "user_id": user["user_id"],
                    "amount": burst_amount,
                    "currency": "USD",
                    "merchant": merchant,
                    "merchant_category": category,
                    "location": "Burst City",
                    "country": user["home_country"],
                    "user_home_country": user["home_country"],
                    "timestamp": (
                        current_time + timedelta(seconds=burst_index * 20)
                    ).isoformat(),
                    "payment_method": "card",
                    "status": "success",
                    "device_id": user["device_id"],
                    "ip_address": user["ip_address"],
                    "channel": "online",
                }

                transactions.append(tx)
                index += 1

        else:
            tx = _base_transaction(index, current_time)

            if random.random() < 0.15:
                tx = _make_suspicious(tx)

            transactions.append(tx)
            index += 1

    return transactions[:count]