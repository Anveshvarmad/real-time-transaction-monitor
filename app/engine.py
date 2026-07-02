from collections import Counter
from typing import Dict, List, Optional

from app.ml_anomaly import MLAnomalyScorer
from app.models import Alert, Transaction
from app.rules import evaluate_rules


class MonitoringEngine:
    def __init__(
        self,
        history_limit: int = 50000,
        enable_ml: bool = True,
    ):
        self.history_limit = history_limit
        self.enable_ml = enable_ml
        self.ml_scorer = MLAnomalyScorer() if enable_ml else None

        self.history: List[Transaction] = []
        self.total_processed = 0
        self.total_alerts = 0
        self.alert_category_counter = Counter()
        self.rule_counter = Counter()

    def process_transaction(self, tx: Transaction) -> Optional[Alert]:
        matched_rules = evaluate_rules(tx, self.history)

        if self.enable_ml and self.ml_scorer is not None:
            ml_rules = self.ml_scorer.evaluate(tx, self.history)
            matched_rules.extend(ml_rules)

        risk_score = min(sum(rule.risk_points for rule in matched_rules), 100)
        alert_category = self._get_alert_category(risk_score)

        self.total_processed += 1

        alert = None

        if risk_score >= 30:
            alert = Alert(
                transaction_id=tx.transaction_id,
                user_id=tx.user_id,
                risk_score=risk_score,
                alert_category=alert_category,
                matched_rules=matched_rules,
                transaction=tx,
            )

            self.total_alerts += 1
            self.alert_category_counter[alert_category] += 1

            for rule in matched_rules:
                self.rule_counter[rule.rule_code] += 1

        if self.enable_ml and self.ml_scorer is not None:
            self.ml_scorer.observe(tx, self.history)

        self.history.append(tx)

        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]

        return alert

    def _get_alert_category(self, risk_score: int) -> str:
        if risk_score >= 70:
            return "HIGH_RISK"

        if risk_score >= 30:
            return "MEDIUM_RISK"

        return "LOW_RISK"

    def summary(self) -> Dict:
        alert_rate = 0

        if self.total_processed > 0:
            alert_rate = round(
                (self.total_alerts / self.total_processed) * 100,
                2,
            )

        return {
            "total_transactions_processed": self.total_processed,
            "total_alerts_generated": self.total_alerts,
            "alert_rate_percent": alert_rate,
            "alert_categories": dict(self.alert_category_counter),
            "top_triggered_rules": dict(self.rule_counter.most_common(10)),
            "ml_enabled": self.enable_ml,
            "ml_trained": (
                self.ml_scorer.is_trained
                if self.ml_scorer is not None
                else False
            ),
        }
