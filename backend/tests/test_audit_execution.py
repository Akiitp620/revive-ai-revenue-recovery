import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models import Payment, FailureEvent, RecoveryAction, RecoveryOutcome, AuditLog, RecoveryPrediction
from app.main import app
from app.database import get_db
from app.core import api_service
from app.core.audit import InvestigationAuditService

client = TestClient(app)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Base

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db_session(monkeypatch):
    """Provides a fresh database session."""
    Base.metadata.create_all(bind=engine)
    
    # Mock the DB dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    session = TestingSessionLocal()
    
    class SessionWrapper:
        def __init__(self, sess):
            self._sess = sess
        def __getattr__(self, name):
            return getattr(self._sess, name)
        def close(self):
            pass # Prevent closing the shared session in agent_tools
            
    monkeypatch.setattr("app.core.agent_tools.SessionLocal", lambda: SessionWrapper(session))
    
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def setup_payment(test_db_session):
    """Creates a failed payment with required relationships."""
    payment = Payment(id=9999, customer_id="cust_123", amount=100.0, status="failed", currency="USD")
    test_db_session.add(payment)
    test_db_session.commit()
    
    failure = FailureEvent(
        payment_id=9999,
        failure_reason="insufficient_funds",
        context_snapshot={}
    )
    test_db_session.add(failure)
    test_db_session.commit()
    
    pred = RecoveryPrediction(
        failure_event_id=failure.id,
        recovery_probability=1.0,
        model_version="1.0",
        feature_snapshot={}
    )
    test_db_session.add(pred)
    test_db_session.commit()
    
    return payment.id

def test_successful_execution_creates_all_records(test_db_session, setup_payment):
    # Seed an investigation
    trace_id = "test_trace_EXEC"
    investigation_id = f"inv_pay_{setup_payment}"
    audit_service = InvestigationAuditService(test_db_session)
    audit_service.log_event(trace_id, investigation_id, f"pay_{setup_payment}", "HUMAN", "POLICY_VALIDATED", {"outcome": "EXECUTE"})
    
    # Execute recovery
    success = api_service.execute_recovery_action(test_db_session, f"pay_{setup_payment}", "RETRY_NOW")
    assert success is True
    
    test_db_session.commit()
    # 1 & 2. RecoveryAction & Outcome created
    action = test_db_session.query(RecoveryAction).first()
    assert action is not None
    assert action.action_type == "RETRY_NOW"
    assert action.status == "EXECUTE"
    
    outcome = test_db_session.query(RecoveryOutcome).first()
    assert outcome is not None
    assert outcome.recovery_action_id == action.id
    
    # 3-6. Correct AuditLog event
    logs = test_db_session.query(AuditLog).filter(AuditLog.event_type == "PAYMENT_RECOVERED").all()
    assert len(logs) == 1
    log = logs[0]
    assert log.investigation_id == investigation_id
    assert log.payment_id == f"pay_{setup_payment}"
    assert log.trace_id == trace_id

def test_review_creates_human_review_requested(test_db_session, setup_payment):
    trace_id = "test_trace_REV"
    investigation_id = f"inv_pay_{setup_payment}"
    audit_service = InvestigationAuditService(test_db_session)
    audit_service.log_event(trace_id, investigation_id, f"pay_{setup_payment}", "HUMAN", "POLICY_VALIDATED", {"outcome": "REVIEW"})
    
    success = api_service.execute_recovery_action(test_db_session, f"pay_{setup_payment}", "HUMAN_REVIEW")
    assert success is True
    
    # 7. REVIEW creates HUMAN_REVIEW_REQUESTED but no terminal recovery event
    action = test_db_session.query(RecoveryAction).first()
    assert action is not None
    assert action.status == "REVIEW"
    
    outcome = test_db_session.query(RecoveryOutcome).first()
    assert outcome is None
    
    logs = test_db_session.query(AuditLog).filter(AuditLog.event_type == "HUMAN_REVIEW_REQUESTED").all()
    assert len(logs) == 1

def test_stop_creates_appropriate_audit_event(test_db_session, setup_payment):
    trace_id = "test_trace_STOP"
    investigation_id = f"inv_pay_{setup_payment}"
    audit_service = InvestigationAuditService(test_db_session)
    audit_service.log_event(trace_id, investigation_id, f"pay_{setup_payment}", "HUMAN", "POLICY_VALIDATED", {"outcome": "STOP"})
    
    success = api_service.execute_recovery_action(test_db_session, f"pay_{setup_payment}", "STOP")
    
    # 8. STOP creates PAYMENT_NOT_RECOVERED
    logs = test_db_session.query(AuditLog).filter(AuditLog.event_type == "PAYMENT_NOT_RECOVERED").all()
    assert len(logs) == 1
    
    outcome = test_db_session.query(RecoveryOutcome).first()
    assert outcome is None

def test_duplicate_execution_is_idempotent(test_db_session, setup_payment):
    trace_id = "test_trace_IDEM"
    investigation_id = f"inv_pay_{setup_payment}"
    audit_service = InvestigationAuditService(test_db_session)
    audit_service.log_event(trace_id, investigation_id, f"pay_{setup_payment}", "HUMAN", "POLICY_VALIDATED", {"outcome": "EXECUTE"})
    
    api_service.execute_recovery_action(test_db_session, f"pay_{setup_payment}", "RETRY_NOW")
    api_service.execute_recovery_action(test_db_session, f"pay_{setup_payment}", "RETRY_NOW")
    
    test_db_session.commit()
    # 10. Duplicate execution does not duplicate terminal audit events
    actions = test_db_session.query(RecoveryAction).all()
    assert len(actions) == 1
    
    logs = test_db_session.query(AuditLog).filter(AuditLog.event_type == "PAYMENT_RECOVERED").all()
    assert len(logs) == 1

def test_get_investigation_state_reconstruction(test_db_session, setup_payment):
    trace_id = "test_trace_STATE"
    investigation_id = f"inv_pay_{setup_payment}"
    audit_service = InvestigationAuditService(test_db_session)
    audit_service.log_event(trace_id, investigation_id, f"pay_{setup_payment}", "HUMAN", "POLICY_VALIDATED", {"outcome": "EXECUTE"})
    
    # 12. State reconstructs correct state from canonical records
    api_service.execute_recovery_action(test_db_session, f"pay_{setup_payment}", "RETRY_NOW")
    
    test_db_session.commit()
    state = api_service.get_investigation_state(test_db_session, investigation_id)
    assert state["final_decision"] == "EXECUTE"
    assert state["recommendation"] == "RETRY_NOW"
