import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st


OUTPUT_DIR = Path("output")
ALERTS_FILE = OUTPUT_DIR / "alerts.jsonl"
TRANSACTIONS_FILE = OUTPUT_DIR / "transactions.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "summary.json"


def load_jsonl(path: Path) -> list:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def load_summary() -> dict:
    if not SUMMARY_FILE.exists():
        return {}

    with SUMMARY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_alert_dataframe(alerts: list) -> pd.DataFrame:
    rows = []

    for alert in alerts:
        transaction = alert.get("transaction", {})
        matched_rules = alert.get("matched_rules", [])

        rows.append({
            "transaction_id": alert.get("transaction_id"),
            "user_id": alert.get("user_id"),
            "risk_score": alert.get("risk_score"),
            "alert_category": alert.get("alert_category"),
            "amount": transaction.get("amount"),
            "merchant": transaction.get("merchant"),
            "merchant_category": transaction.get("merchant_category"),
            "country": transaction.get("country"),
            "payment_method": transaction.get("payment_method"),
            "channel": transaction.get("channel"),
            "matched_rules": ", ".join(
                rule.get("rule_code", "") for rule in matched_rules
            ),
        })

    return pd.DataFrame(rows)


def build_transaction_dataframe(transactions: list) -> pd.DataFrame:
    if not transactions:
        return pd.DataFrame()

    return pd.DataFrame(transactions)


def get_rule_counts(alerts: list) -> pd.DataFrame:
    counter = Counter()

    for alert in alerts:
        for rule in alert.get("matched_rules", []):
            counter[rule.get("rule_code")] += 1

    rows = [
        {"rule": rule, "count": count}
        for rule, count in counter.most_common(10)
    ]

    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(
        page_title="Transaction Monitoring Dashboard",
        page_icon="📊",
        layout="wide",
    )

    st.title("Real-Time Transaction Monitoring System")
    st.caption(
        "Local zero-cost dashboard for transaction anomaly detection, "
        "risk scoring, and alert analysis."
    )

    summary = load_summary()
    alerts = load_jsonl(ALERTS_FILE)
    transactions = load_jsonl(TRANSACTIONS_FILE)

    if not summary:
        st.warning(
            "No monitoring output found. Run this command first: "
            "`python -m app.main --count 10000 --output output`"
        )
        return

    total_transactions = summary.get("total_transactions_processed", 0)
    total_alerts = summary.get("total_alerts_generated", 0)
    alert_rate = summary.get("alert_rate_percent", 0)

    high_risk_count = summary.get("alert_categories", {}).get("HIGH_RISK", 0)
    medium_risk_count = summary.get("alert_categories", {}).get("MEDIUM_RISK", 0)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Transactions Processed", f"{total_transactions:,}")
    col2.metric("Alerts Generated", f"{total_alerts:,}")
    col3.metric("Alert Rate", f"{alert_rate}%")
    col4.metric("High Risk Alerts", f"{high_risk_count:,}")

    st.divider()

    alert_df = build_alert_dataframe(alerts)
    transaction_df = build_transaction_dataframe(transactions)
    rule_df = get_rule_counts(alerts)

    left, right = st.columns(2)

    with left:
        st.subheader("Alert Categories")

        category_data = pd.DataFrame([
            {"category": "HIGH_RISK", "count": high_risk_count},
            {"category": "MEDIUM_RISK", "count": medium_risk_count},
        ])

        if not category_data.empty:
            st.bar_chart(
                category_data,
                x="category",
                y="count",
            )

    with right:
        st.subheader("Top Triggered Rules")

        if not rule_df.empty:
            st.bar_chart(
                rule_df,
                x="rule",
                y="count",
            )
        else:
            st.info("No triggered rules found.")

    st.divider()

    st.subheader("Recent Alerts")

    if alert_df.empty:
        st.info("No alerts generated.")
    else:
        category_filter = st.multiselect(
            "Filter by alert category",
            options=sorted(alert_df["alert_category"].dropna().unique()),
            default=sorted(alert_df["alert_category"].dropna().unique()),
        )

        filtered_alerts = alert_df[
            alert_df["alert_category"].isin(category_filter)
        ]

        st.dataframe(
            filtered_alerts.sort_values(
                by="risk_score",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Transaction Sample")

    if transaction_df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(
            transaction_df.head(100),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()