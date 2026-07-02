from datetime import datetime

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_high_risk_transaction_ingestion():
    payload = {
        "transaction_id": "TXN_API_001",
        "user_id": "U_API_TEST",
        "amount": 7500,
        "currency": "USD",
        "merchant": "CryptoX",
        "merchant_category": "crypto",
        "location": "New York",
        "country": "US",
        "user_home_country": "US",
        "timestamp": datetime.now().isoformat(),
        "payment_method": "card",
        "status": "success",
        "device_id": "D_API_TEST",
        "ip_address": "127.0.0.1",
        "channel": "online",
    }

    response = client.post("/transactions", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["transaction_id"] == "TXN_API_001"
    assert body["alert_generated"] is True
    assert body["risk_score"] >= 30
    assert body["alert"] is not None


def test_bulk_transaction_ingestion():
    payload = {
        "transactions": [
            {
                "transaction_id": "TXN_BULK_001",
                "user_id": "U_BULK_TEST",
                "amount": 50,
                "currency": "USD",
                "merchant": "Walmart",
                "merchant_category": "retail",
                "location": "New York",
                "country": "US",
                "user_home_country": "US",
                "timestamp": datetime.now().isoformat(),
                "payment_method": "card",
                "status": "success",
                "device_id": "D_BULK_TEST",
                "ip_address": "127.0.0.2",
                "channel": "pos",
            },
            {
                "transaction_id": "TXN_BULK_002",
                "user_id": "U_BULK_TEST",
                "amount": 9000,
                "currency": "USD",
                "merchant": "GoldHouse",
                "merchant_category": "jewelry",
                "location": "New York",
                "country": "US",
                "user_home_country": "US",
                "timestamp": datetime.now().isoformat(),
                "payment_method": "card",
                "status": "success",
                "device_id": "D_BULK_TEST",
                "ip_address": "127.0.0.2",
                "channel": "online",
            },
        ]
    }

    response = client.post("/transactions/bulk", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["total_received"] == 2
    assert body["total_alerts"] >= 1
