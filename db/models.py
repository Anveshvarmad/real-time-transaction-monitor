from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TransactionRecord(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10))
    merchant: Mapped[str] = mapped_column(String(255), index=True)
    merchant_category: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(20), index=True)
    user_home_country: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    payment_method: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    device_id: Mapped[str] = mapped_column(String(100), index=True)
    ip_address: Mapped[str] = mapped_column(String(100), index=True)
    channel: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    alerts: Mapped[list["AlertRecord"]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
    )


class AlertRecord(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("transactions.transaction_id"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    alert_category: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transaction: Mapped["TransactionRecord"] = relationship(back_populates="alerts")

    rule_matches: Mapped[list["RuleMatchRecord"]] = relationship(
        back_populates="alert",
        cascade="all, delete-orphan",
    )


class RuleMatchRecord(Base):
    __tablename__ = "rule_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("alerts.id"),
        index=True,
    )
    rule_code: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text)
    risk_points: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    alert: Mapped["AlertRecord"] = relationship(back_populates="rule_matches")
