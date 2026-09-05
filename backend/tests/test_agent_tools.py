import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from app.models import Base, Payment, Customer, Merchant, PaymentAttempt, FailureEvent, RecoveryAction
from app.core.agent_tools import (
    get_payment, get_customer_history, get_payment_attempts,
    get_failure_context, get_merchant_policy, simulate_recovery_action,
    record_recovery_action
)
import app.core.agent_tools

# Use in-memory SQLite for testing
engine = create_engine(
    "sqlite:///file:memdb2?mode=memory&cache=shared",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Patch the SessionLocal in agent_tools to return our test session
    monkeypatch.setattr(app.core.agent_tools, "SessionLocal", lambda: db)
    
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def seed_data(db_session):
    m = Merchant(name="Test Merchant")
    db_session.add(m)
    db_session.flush()
    
    c = Customer(merchant_id=m.id, external_id="cust_123")
    db_session.add(c)
    db_session.flush()
    
    dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
    p = Payment(customer_id=c.id, amount=150.0, currency="USD", status="failed", created_at=dt)
    db_session.add(p)
    db_session.flush()
    
    # Add a successful payment for customer history computation
    p_success = Payment(customer_id=c.id, amount=200.0, currency="USD", status="success", created_at=dt)
    db_session.add(p_success)
    db_session.flush()
    
    att = PaymentAttempt(payment_id=p.id, status="failed", error_code="insufficient_funds")
    db_session.add(att)
    
    fe = FailureEvent(payment_id=p.id, failure_reason="insufficient_funds", context_snapshot={"device": "mobile"})
    db_session.add(fe)
    db_session.flush()
    
    from app.models import RecoveryPrediction
    rp = RecoveryPrediction(failure_event_id=fe.id, model_version="test_v1", feature_snapshot={}, recovery_probability=0.7)
    db_session.add(rp)
    
    db_session.commit()
    return {"payment_id": f"pay_{p.id}", "db_id": p.id, "customer_id": c.external_id}

def test_get_payment(db_session, seed_data):
    result = get_payment(seed_data["payment_id"])
    assert result["payment_id"] == seed_data["payment_id"]
    assert result["amount"] == 150.0
    assert result["status"] == "failed"

def test_get_payment_not_found(db_session):
    with pytest.raises(ValueError, match="not found in database"):
        get_payment("pay_9999")

def test_get_customer_history(db_session, seed_data):
    result = get_customer_history(seed_data["payment_id"])
    assert result["customer_id"] == seed_data["customer_id"]
    assert result["lifetime_value"] == 200.0
    assert result["success_rate"] == 0.5  # 1 success out of 2 payments

def test_get_payment_attempts(db_session, seed_data):
    attempts = get_payment_attempts(seed_data["payment_id"])
    assert len(attempts) == 1
    assert attempts[0]["error_code"] == "insufficient_funds"

def test_get_failure_context(db_session, seed_data):
    ctx = get_failure_context(seed_data["payment_id"])
    assert ctx["error_code"] == "insufficient_funds"
    assert ctx["context"]["device"] == "mobile"

def test_get_merchant_policy():
    policy = get_merchant_policy("any")
    assert "allowlist" in policy
    assert "retry_limit" in policy
    assert "human_approval_threshold" in policy

def test_simulate_recovery_action(db_session, seed_data):
    res = simulate_recovery_action("RETRY_LATER", seed_data["payment_id"])
    assert res["action"] == "RETRY_LATER"
    assert "expected_recovery" in res
    assert "expected_net_recovery" in res
    assert res["probability"] == 0.7  # directly matches the seeded RecoveryPrediction
    assert res["policy_status"] == "allowed"

def test_simulate_recovery_action_multipliers(db_session, seed_data):
    res = simulate_recovery_action("RETRY_NOW", seed_data["payment_id"])
    assert res["probability"] == 0.7 * 0.5
    
    res = simulate_recovery_action("STOP", seed_data["payment_id"])
    assert res["probability"] == 0.0

def test_simulate_recovery_action_missing_prediction(db_session):
    # Payment without FailureEvent and RecoveryPrediction
    p = Payment(customer_id=1, amount=100.0)
    db_session.add(p)
    db_session.commit()
    
    res = simulate_recovery_action("RETRY_LATER", f"pay_{p.id}")
    assert res == {"unavailable": True, "reason": "No recovery prediction found", "policy_status": "allowed"}

def test_record_recovery_action(db_session, seed_data):
    res = record_recovery_action(seed_data["payment_id"], "RETRY_LATER", "pending")
    assert res["status"] == "recorded"
    assert "action_id" in res
    
    # Verify in DB
    action = db_session.query(RecoveryAction).filter(RecoveryAction.id == res["action_id"]).first()
    assert action is not None
    assert action.action_type == "RETRY_LATER"
    assert action.status == "pending"

def test_record_recovery_action_missing_event(db_session):
    # Payment without FailureEvent
    p = Payment(customer_id=1, amount=100.0)
    db_session.add(p)
    db_session.commit()
    
    with pytest.raises(ValueError, match="Cannot record action: FailureEvent not found"):
        record_recovery_action(f"pay_{p.id}", "RETRY_LATER", "pending")
