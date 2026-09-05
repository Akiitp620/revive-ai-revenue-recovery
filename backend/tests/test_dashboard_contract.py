import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from app.core.api_service import get_dashboard_metrics
from app.models import Base, Payment, FailureEvent, RecoveryAction, RecoveryPrediction, Merchant
from app.core.policy import DeterministicPolicyEngine

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def seed_data(db_session):
    m = Merchant(name="Test Merchant")
    db_session.add(m)
    db_session.flush()
    p = Payment(customer_id=1, amount=100.0, currency="USD", status="failed")
    db_session.add(p)
    db_session.flush()
    fe = FailureEvent(payment_id=p.id, failure_reason="insufficient_funds")
    db_session.add(fe)
    db_session.commit()
    return {"merchant_id": m.id, "payment_id": p.id, "db_id": fe.id}

def test_dashboard_contract_missing_data(db_session):
    # Test with no data
    data = get_dashboard_metrics(db_session)
    
    # baselineComparison must be null/None
    assert data["baselineComparison"] is None
    
    # efficiency should exist but reflect 0% where applicable
    assert data["efficiency"] is not None
    assert len(data["efficiency"]) == 4
    assert data["efficiency"][0]["value"] == "0.0%"  # Recovery Rate
    assert data["efficiency"][1]["value"] == "0"     # Actions Executed
    assert data["efficiency"][2]["value"] == "0.0%"  # Escalation Rate
    assert data["efficiency"][3]["value"] == "0"     # Hard Declines Stopped
    
    # insight must be a valid structure even when there are no opportunities
    assert data["insight"] is not None
    assert data["insight"]["revenueOpportunity"] == 0
    
    # guardrails must reflect the DeterministicPolicyEngine
    engine = DeterministicPolicyEngine()
    assert data["guardrails"] is not None
    assert len(data["guardrails"]) == 4
    assert data["guardrails"][0]["rule"] == "Max Retries Allowed"
    assert data["guardrails"][0]["value"] == str(engine.MAX_RETRIES)

    # paymentHealth must be an empty list as we don't have payment method metrics
    assert data["paymentHealth"] == []

def test_dashboard_contract_with_data(db_session, seed_data):
    # Seed data provides a Payment and FailureEvent.
    # Add a RecoveryPrediction to create an opportunity.
    fe_id = seed_data["db_id"]
    p = RecoveryPrediction(failure_event_id=fe_id, model_version="v1", feature_snapshot={}, recovery_probability=0.5)
    db_session.add(p)
    
    # Add an executed action
    action = RecoveryAction(failure_event_id=fe_id, action_type="HUMAN_REVIEW", status="completed")
    db_session.add(action)
    db_session.commit()
    
    data = get_dashboard_metrics(db_session)
    
    # insight should now exist
    assert data["insight"] is not None
    assert "revenueOpportunity" in data["insight"]
    
    # efficiency should reflect the 1 executed action
    assert data["efficiency"][1]["value"] == "1"
    # Escalation Rate should be 100.0% (1/1)
    assert data["efficiency"][2]["value"] == "100.0%"

    # recoveryQueue must have the correct schema to avoid frontend TypeError
    assert len(data["recoveryQueue"]) > 0
    item = data["recoveryQueue"][0]
    assert "transactionId" in item
    assert "amount" in item
    assert "failureReason" in item
    assert "recoveryProbability" in item
    assert "expectedRecovery" in item
    assert "recommendation" in item
    assert "status" in item
