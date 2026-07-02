import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from collections import Counter
from decimal import Decimal

import pandas as pd
import streamlit as st

from db.models import AlertRecord, RuleMatchRecord, TransactionRecord
from db.session import SessionLocal, initialize_database


def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def load_summary() -> dict:
    initialize_database()
    session = SessionLocal()

    try:
        total_transactions = session.query(TransactionRecord).count()
        total_alerts = session.query(AlertRecord).count()

        alert_rate = 0
        if total_transactions > 0:
            alert_rate = round((total_alerts / total_transactions) * 100, 2)

        alert_categories = {}
        category_rows = (
            session.query(
                AlertRecord.alert_category,
            )
            .all()
        )

        category_counter = Counter(row.alert_category for row in category_rows)
        alert_categories = dict(category_counter)

        rule_rows = (
            session.query(RuleMatchRecord.rule_code)
            .all()
        )

        rule_counter = Counter(row.rule_code for row in rule_rows)

        return {
            "total_transactions_processed": total_transactions,
            "total_alerts_generated": total_alerts,
            "alert_rate_percent": alert_rate,
            "alert_categories": alert_categories,
            "top_triggered_rules": dict(rule_counter.most_common(10)),
        }

    finally:
        session.close()


def load_recent_alerts(limit: int = 500) -> pd.DataFrame:
    initialize_database()
    session = SessionLocal()

    try:
        alerts = (
            session.query(AlertRecord)
            .join(TransactionRecord)
            .order_by(AlertRecord.created_at.desc())
            .limit(limit)
            .all()
        )

        rows = []

        for alert in alerts:
            tx = alert.transaction
            matched_rules = ", ".join(
                rule.rule_code for rule in alert.rule_matches
            )

            rows.append({
                "transaction_id": alert.transaction_id,
                "user_id": alert.user_id,
                "risk_score": alert.risk_score,
                "alert_category": alert.alert_category,
                "amount": decimal_to_float(tx.amount),
                "merchant": tx.merchant,
                "merchant_category": tx.merchant_category,
                "country": tx.country,
                "payment_method": tx.payment_method,
                "channel": tx.channel,
                "matched_rules": matched_rules,
                "created_at": alert.created_at,
            })

        return pd.DataFrame(rows)

    finally:
        session.close()


def load_recent_transactions(limit: int = 300) -> pd.DataFrame:
    initialize_database()
    session = SessionLocal()

    try:
        transactions = (
            session.query(TransactionRecord)
            .order_by(TransactionRecord.created_at.desc())
            .limit(limit)
            .all()
        )

        rows = []

        for tx in transactions:
            rows.append({
                "transaction_id": tx.transaction_id,
                "user_id": tx.user_id,
                "amount": decimal_to_float(tx.amount),
                "currency": tx.currency,
                "merchant": tx.merchant,
                "merchant_category": tx.merchant_category,
                "country": tx.country,
                "timestamp": tx.timestamp,
                "payment_method": tx.payment_method,
                "status": tx.status,
                "channel": tx.channel,
                "created_at": tx.created_at,
            })

        return pd.DataFrame(rows)

    finally:
        session.close()


def load_top_suspicious_users(limit: int = 10) -> pd.DataFrame:
    initialize_database()
    session = SessionLocal()

    try:
        alerts = session.query(AlertRecord).all()
        counter = Counter(alert.user_id for alert in alerts)

        rows = [
            {"user_id": user_id, "alert_count": count}
            for user_id, count in counter.most_common(limit)
        ]

        return pd.DataFrame(rows)

    finally:
        session.close()


def load_high_risk_merchants(limit: int = 10) -> pd.DataFrame:
    initialize_database()
    session = SessionLocal()

    try:
        alerts = (
            session.query(AlertRecord)
            .join(TransactionRecord)
            .all()
        )

        counter = Counter(alert.transaction.merchant for alert in alerts)

        rows = [
            {"merchant": merchant, "alert_count": count}
            for merchant, count in counter.most_common(limit)
        ]

        return pd.DataFrame(rows)

    finally:
        session.close()


def main() -> None:
    st.set_page_config(
        page_title="Fraud Monitoring Dashboard",
        page_icon="📊",
        layout="wide",
    )

    st.title("Real-Time Fraud Detection and Transaction Monitoring Platform")
    st.caption(
        "Database-backed dashboard for transaction ingestion, anomaly rules, "
        "risk scoring, and alert investigation."
    )

    summary = load_summary()

    total_transactions = summary.get("total_transactions_processed", 0)
    total_alerts = summary.get("total_alerts_generated", 0)
    alert_rate = summary.get("alert_rate_percent", 0)
    alert_categories = summary.get("alert_categories", {})

    if total_transactions == 0:
        st.warning(
            "No transaction data found in PostgreSQL. Send data using: "
            "`python -m simulator.send_transactions --count 300 --batch-size 25`"
        )
        return

    high_risk_count = alert_categories.get("HIGH_RISK", 0)
    medium_risk_count = alert_categories.get("MEDIUM_RISK", 0)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Transactions Processed", f"{total_transactions:,}")
    col2.metric("Alerts Generated", f"{total_alerts:,}")
    col3.metric("Alert Rate", f"{alert_rate}%")
    col4.metric("High Risk Alerts", f"{high_risk_count:,}")

    st.divider()

    recent_alerts_df = load_recent_alerts()
    recent_transactions_df = load_recent_transactions()
    suspicious_users_df = load_top_suspicious_users()
    risky_merchants_df = load_high_risk_merchants()

    left, right = st.columns(2)

    with left:
        st.subheader("Alert Categories")

        category_df = pd.DataFrame([
            {"category": "HIGH_RISK", "count": high_risk_count},
            {"category": "MEDIUM_RISK", "count": medium_risk_count},
        ])

        st.bar_chart(category_df, x="category", y="count")

    with right:
        st.subheader("Top Triggered Rules")

        top_rules = summary.get("top_triggered_rules", {})
        rule_df = pd.DataFrame([
            {"rule": rule, "count": count}
            for rule, count in top_rules.items()
        ])

        if rule_df.empty:
            st.info("No rule matches found.")
        else:
            st.bar_chart(rule_df, x="rule", y="count")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Most Suspicious Users")

        if suspicious_users_df.empty:
            st.info("No suspicious users found.")
        else:
            st.dataframe(
                suspicious_users_df,
                use_container_width=True,
                hide_index=True,
            )

    with right:
        st.subheader("Highest-Risk Merchants")

        if risky_merchants_df.empty:
            st.info("No risky merchants found.")
        else:
            st.dataframe(
                risky_merchants_df,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.subheader("Recent Alerts")

    if recent_alerts_df.empty:
        st.info("No alerts generated.")
    else:
        category_filter = st.multiselect(
            "Filter by alert category",
            options=sorted(recent_alerts_df["alert_category"].dropna().unique()),
            default=sorted(recent_alerts_df["alert_category"].dropna().unique()),
        )

        filtered_alerts = recent_alerts_df[
            recent_alerts_df["alert_category"].isin(category_filter)
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

    st.subheader("Recent Transactions")

    if recent_transactions_df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(
            recent_transactions_df,
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
