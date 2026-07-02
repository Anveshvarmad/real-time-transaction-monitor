from app.rule_config import load_rule_config


def test_rule_config_loads_yaml():
    config = load_rule_config()

    high_amount_rule = config.get_rule("HIGH_AMOUNT")

    assert high_amount_rule.enabled is True
    assert high_amount_rule.risk_points == 30
    assert high_amount_rule.category == "amount"
    assert config.get_param("HIGH_AMOUNT", "threshold") == 5000


def test_rule_config_builds_rule_result():
    config = load_rule_config()

    result = config.build_result("HIGH_AMOUNT")

    assert result.rule_code == "HIGH_AMOUNT"
    assert result.risk_points == 30
    assert result.category == "amount"