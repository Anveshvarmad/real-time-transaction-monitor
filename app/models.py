from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class Transaction:
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant: str
    merchant_category: str
    location: str
    country: str
    user_home_country: str
    timestamp: datetime
    payment_method: str
    status: str
    device_id: str
    ip_address: str
    channel: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        payload = data.copy()

        if isinstance(payload["timestamp"], str):
            payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])

        return cls(**payload)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


@dataclass
class RuleResult:
    rule_code: str
    description: str
    risk_points: int
    category: str


@dataclass
class Alert:
    transaction_id: str
    user_id: str
    risk_score: int
    alert_category: str
    matched_rules: List[RuleResult]
    transaction: Transaction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "risk_score": self.risk_score,
            "alert_category": self.alert_category,
            "matched_rules": [asdict(rule) for rule in self.matched_rules],
            "transaction": self.transaction.to_dict(),
        }