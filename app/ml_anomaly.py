from typing import List

import numpy as np
from sklearn.ensemble import IsolationForest

from app.ml_features import extract_features
from app.models import RuleResult, Transaction
from app.rule_config import load_rule_config


class MLAnomalyScorer:
    def __init__(self):
        config = load_rule_config()

        self.min_training_samples = int(
            config.get_param(
                "ML_ANOMALY_SCORE",
                "min_training_samples",
                75,
            )
        )
        self.contamination = float(
            config.get_param(
                "ML_ANOMALY_SCORE",
                "contamination",
                0.08,
            )
        )
        self.random_state = int(
            config.get_param(
                "ML_ANOMALY_SCORE",
                "random_state",
                42,
            )
        )
        self.high_risk_threshold = float(
            config.get_param(
                "ML_HIGH_RISK_PATTERN",
                "anomaly_score_threshold",
                -0.08,
            )
        )

        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
        )

        self.training_rows: List[List[float]] = []
        self.is_trained = False
        self.transactions_seen = 0

    def observe(
        self,
        tx: Transaction,
        history: List[Transaction],
    ) -> None:
        features = extract_features(tx, history)
        self.training_rows.append(features)
        self.transactions_seen += 1

        if len(self.training_rows) > 5000:
            self.training_rows = self.training_rows[-5000:]

        if not self.is_trained and len(self.training_rows) >= self.min_training_samples:
            self._fit_model()

        if self.is_trained and self.transactions_seen % 500 == 0:
            self._fit_model()

    def evaluate(
        self,
        tx: Transaction,
        history: List[Transaction],
    ) -> List[RuleResult]:
        config = load_rule_config()
        matched: List[RuleResult] = []

        if not config.is_enabled("ML_ANOMALY_SCORE"):
            return matched

        if not self.is_trained:
            return matched

        features = np.array([extract_features(tx, history)])
        prediction = self.model.predict(features)[0]
        anomaly_score = float(self.model.decision_function(features)[0])

        if prediction == -1:
            matched.append(config.build_result("ML_ANOMALY_SCORE"))

        if (
            config.is_enabled("ML_HIGH_RISK_PATTERN")
            and anomaly_score < self.high_risk_threshold
        ):
            matched.append(config.build_result("ML_HIGH_RISK_PATTERN"))

        return matched

    def _fit_model(self) -> None:
        training_matrix = np.array(self.training_rows)
        self.model.fit(training_matrix)
        self.is_trained = True
