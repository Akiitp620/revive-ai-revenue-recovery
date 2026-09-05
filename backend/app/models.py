from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def now_utc():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)
    updated_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        onupdate=now_utc,
        nullable=False)

    customers = relationship("Customer", back_populates="merchant")
    policies = relationship("MerchantPolicy", back_populates="merchant")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(
        Integer,
        ForeignKey("merchants.id"),
        nullable=False,
        index=True)
    external_id = Column(
        String(255),
        nullable=False,
        index=True)  # ID from the merchant's system
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)
    updated_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        onupdate=now_utc,
        nullable=False)

    merchant = relationship("Merchant", back_populates="customers")
    payments = relationship("Payment", back_populates="customer")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)
    updated_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        onupdate=now_utc,
        nullable=False)

    customer = relationship("Customer", back_populates="payments")
    attempts = relationship("PaymentAttempt", back_populates="payment")
    failure_events = relationship("FailureEvent", back_populates="payment")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False,
        index=True)
    attempt_time = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)
    status = Column(String(50), nullable=False)  # e.g., 'success', 'failed'
    error_code = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    payment = relationship("Payment", back_populates="attempts")


class FailureEvent(Base):
    __tablename__ = "failure_events"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False,
        index=True)
    failure_reason = Column(String(255), nullable=False)
    # e.g., device, ip, time of day
    context_snapshot = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    payment = relationship("Payment", back_populates="failure_events")
    predictions = relationship(
        "RecoveryPrediction",
        back_populates="failure_event")
    actions = relationship("RecoveryAction", back_populates="failure_event")
    evaluation_cases = relationship(
        "EvaluationCase",
        back_populates="failure_event")


class RecoveryPrediction(Base):
    __tablename__ = "recovery_predictions"

    id = Column(Integer, primary_key=True, index=True)
    failure_event_id = Column(
        Integer,
        ForeignKey("failure_events.id"),
        nullable=False,
        index=True)
    model_version = Column(String(100), nullable=False)
    # reproducible prediction inputs
    feature_snapshot = Column(JSON, nullable=False)
    recovery_probability = Column(Float, nullable=False)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    failure_event = relationship("FailureEvent", back_populates="predictions")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    failure_event_id = Column(
        Integer,
        ForeignKey("failure_events.id"),
        nullable=False,
        index=True)
    action_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    failure_event = relationship("FailureEvent", back_populates="actions")
    outcome = relationship(
        "RecoveryOutcome",
        back_populates="action",
        uselist=False)


class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    recovery_action_id = Column(
        Integer,
        ForeignKey("recovery_actions.id"),
        nullable=False,
        unique=True)
    success = Column(Boolean, nullable=False)
    amount_recovered = Column(Float, nullable=False, default=0.0)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    action = relationship("RecoveryAction", back_populates="outcome")


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(
        Integer,
        ForeignKey("merchants.id"),
        nullable=False,
        index=True)
    policy_version = Column(String(100), nullable=False)
    rules_snapshot = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    merchant = relationship("Merchant", back_populates="policies")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(100), nullable=False, index=True)
    investigation_id = Column(String(100), nullable=False, index=True)
    payment_id = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    metadata_snapshot = Column(JSON, nullable=True)
    timestamp = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)


class EvaluationCase(Base):
    """
    Ground truth storage, separate from production data.
    """
    __tablename__ = "evaluation_cases"

    id = Column(Integer, primary_key=True, index=True)
    failure_event_id = Column(
        Integer,
        ForeignKey("failure_events.id"),
        nullable=False,
        index=True)
    ground_truth_outcome = Column(Boolean, nullable=False)
    ground_truth_amount = Column(Float, nullable=False)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    failure_event = relationship(
        "FailureEvent",
        back_populates="evaluation_cases")
    results = relationship("EvaluationResult", back_populates="case")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_case_id = Column(
        Integer,
        ForeignKey("evaluation_cases.id"),
        nullable=False,
        index=True)
    model_version = Column(String(100), nullable=False)
    # Based on some threshold of probability
    predicted_outcome = Column(Boolean, nullable=False)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    case = relationship("EvaluationCase", back_populates="results")


class EvaluationRun(Base):
    """
    Metadata for an entire evaluation execution.
    """
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(100), nullable=False)
    policy_version = Column(String(100), nullable=False)
    dataset_version = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(
            timezone=True),
        default=now_utc,
        nullable=False)

    metrics = relationship("EvaluationRunMetric", back_populates="run")


class EvaluationRunMetric(Base):
    """
    Stored summary results and metrics for an evaluation run.
    """
    __tablename__ = "evaluation_run_metrics"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(
        Integer,
        ForeignKey("evaluation_runs.id"),
        nullable=False,
        index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)

    run = relationship("EvaluationRun", back_populates="metrics")
