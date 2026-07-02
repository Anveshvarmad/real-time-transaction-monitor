import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

from app.models import RuleResult


@dataclass
class RuleDefinition:
    code: str
    enabled: bool
    description: str
    risk_points: int
    category: str
    params: Dict[str, Any]


class RuleConfig:
    def __init__(self, data: Dict[str, Any]):
        self.settings = data.get("settings", {})
        self.rules = data.get("rules", {})

    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)

    def get_rule(self, code: str) -> RuleDefinition:
        raw_rule = self.rules.get(code, {})

        return RuleDefinition(
            code=code,
            enabled=raw_rule.get("enabled", False),
            description=raw_rule.get("description", code),
            risk_points=int(raw_rule.get("risk_points", 0)),
            category=raw_rule.get("category", "general"),
            params=raw_rule.get("params", {}) or {},
        )

    def is_enabled(self, code: str) -> bool:
        return self.get_rule(code).enabled

    def get_param(self, code: str, key: str, default=None):
        return self.get_rule(code).params.get(key, default)

    def build_result(self, code: str) -> RuleResult:
        rule = self.get_rule(code)

        return RuleResult(
            rule_code=rule.code,
            description=rule.description,
            risk_points=rule.risk_points,
            category=rule.category,
        )


@lru_cache(maxsize=1)
def load_rule_config() -> RuleConfig:
    config_path = Path(
        os.getenv("RULE_CONFIG_PATH", "configs/rules.yaml")
    )

    if not config_path.exists():
        raise FileNotFoundError(
            f"Rule config file not found at {config_path}. "
            "Set RULE_CONFIG_PATH or create configs/rules.yaml."
        )

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    return RuleConfig(data)