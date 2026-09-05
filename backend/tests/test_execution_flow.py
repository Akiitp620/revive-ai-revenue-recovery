import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from datetime import datetime, timezone
from app.models import Base, Payment, FailureEvent, RecoveryPrediction, RecoveryAction, RecoveryOutcome, AuditLog
from app.core.simulator import ActionSimulator
from app.core import agent_tools, api_service
import app.core.agent_tools
engine = create_engine(
    "sqlite:///test_execution.db",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db(monkeypatch):
    from app.models import Merchant, Customer, PaymentAttempt
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    monkeypatch.setattr(app.core.agent_tools, "SessionLocal", TestingSessionLocal)
    
    # Insert basic records
    m = Merchant(name="Test Merchant")
    db.add(m)
    db.flush()
    
    c = Customer(merchant_id=m.id, external_id="cust_123")
    db.add(c)
    db.flush()
    
    dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
    payment = Payment(customer_id=c.id, amount=100.0, currency="USD", status="failed", created_at=dt)
    db.add(payment)
    db.commit()
    
    failure = FailureEvent(payment_id=payment.id, failure_reason="insufficient_funds", context_snapshot={"device": "mobile"})
    db.add(failure)
    db.commit()
    
    from app.models import RecoveryPrediction
    pred = RecoveryPrediction(failure_event_id=failure.id, recovery_probability=0.9, feature_snapshot={}, model_version="1.0")
    db.add(pred)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_simulate_operational_outcome():
    class DummyPrediction:
        recovery_probability = 0.8
        
    sim = ActionSimulator()
    
    # 0.8 >= 0.5 -> Success
    res = sim.simulate_operational_outcome("RETRY_LATER", 100.0, DummyPrediction())
    assert res["success"] is True
    assert res["amount_recovered"] == 100.0
    
    # RETRY_NOW halving -> 0.4 < 0.5 -> Failure
    res2 = sim.simulate_operational_outcome("RETRY_NOW", 100.0, DummyPrediction())
    assert res2["success"] is False
    assert res2["amount_recovered"] == 0.0
    
    # STOP -> 0.0 < 0.5 -> Failure
    res3 = sim.simulate_operational_outcome("STOP", 100.0, DummyPrediction())
    assert res3["success"] is False
    assert res3["amount_recovered"] == 0.0

def test_record_recovery_action_execute(db: Session):
    payment = db.query(Payment).first()
    failure = db.query(FailureEvent).filter(FailureEvent.payment_id == payment.id).first()
    
    # Ensure prediction exists
    pred = db.query(RecoveryPrediction).filter(RecoveryPrediction.failure_event_id == failure.id).first()
    assert pred is not None
        
    payment_id_str = f"pay_{payment.id}"
    
    # Test EXECUTE
    action = db.query(RecoveryAction).filter(RecoveryAction.failure_event_id == failure.id).first()
    if action:
        db.query(RecoveryOutcome).filter(RecoveryOutcome.recovery_action_id == action.id).delete()
        db.query(RecoveryAction).filter(RecoveryAction.id == action.id).delete()
        db.commit()
    res = agent_tools.record_recovery_action(payment_id_str, "RETRY_LATER", "EXECUTE", db_session=db)
    assert res["status"] == "recorded"
    assert res["success"] is True
    assert res["amount_recovered"] == float(payment.amount)
    
    # Check DB
    action_rec = db.query(RecoveryAction).filter(RecoveryAction.id == res["action_id"]).first()
    assert action_rec is not None
    assert action_rec.action_type == "RETRY_LATER"
    
    outcome_rec = db.query(RecoveryOutcome).filter(RecoveryOutcome.recovery_action_id == res["action_id"]).first()
    assert outcome_rec is not None
    assert outcome_rec.success is True
    assert outcome_rec.amount_recovered == float(payment.amount)

def test_record_recovery_action_idempotency(db: Session):
    payment = db.query(Payment).first()
    payment_id_str = f"pay_{payment.id}"
    
    res1 = agent_tools.record_recovery_action(payment_id_str, "ALTERNATE_PAYMENT", "EXECUTE", db_session=db)
    res2 = agent_tools.record_recovery_action(payment_id_str, "ALTERNATE_PAYMENT", "EXECUTE", db_session=db)
    
    assert res2["status"] == "already_recorded"
    assert res2["action_id"] == res1["action_id"]

def test_execute_recovery_action_audit(db: Session):
    payment = db.query(Payment).first()
    payment_id_str = f"pay_{payment.id}"
    
    # First need an investigation log to attach to
    log = AuditLog(
        trace_id="test_trace",
        investigation_id="test_inv",
        payment_id=payment_id_str,
        actor="SYSTEM",
        event_type="INVESTIGATION_STARTED"
    )
    db.add(log)
    db.commit()
    
    api_service.execute_recovery_action(db, payment_id_str, "STOP")
    
    # Verify Audit log
    stop_log = db.query(AuditLog).filter(
        AuditLog.payment_id == payment_id_str,
        AuditLog.event_type == "PAYMENT_NOT_RECOVERED"
    ).order_by(AuditLog.timestamp.desc()).first()
    
    assert stop_log is not None
    assert stop_log.metadata_snapshot["final_decision"] == "STOP"
