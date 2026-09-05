from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import engine, Base
from app.models import Payment, PaymentAttempt, FailureEvent, RecoveryPrediction, RecoveryAction, RecoveryOutcome, Customer, Merchant
from datetime import datetime, timezone
import pytest

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    from app.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()

def test_dashboard_baseline_dynamic(setup_db, db_session: Session):
    # Setup single payment with attempt
    merchant = Merchant(name="Test Merchant")
    db_session.add(merchant)
    db_session.commit()
    
    customer = Customer(merchant_id=merchant.id, external_id="CUST-1")
    db_session.add(customer)
    db_session.commit()

    payment = Payment(amount=100.0, status="failed", customer_id=customer.id)
    db_session.add(payment)
    db_session.commit()

    attempt = PaymentAttempt(payment_id=payment.id, status="failed", error_code="insufficient_funds")
    db_session.add(attempt)
    
    event = FailureEvent(payment_id=payment.id, failure_reason="insufficient_funds")
    db_session.add(event)
    db_session.commit()

    # Prediction probability = 0.8
    # Baseline for "insufficient_funds" is "wait_for_paycheck" -> "RETRY_LATER"
    # For RETRY_LATER, ActionSimulator uses base_prob. So prob = 0.8.
    prediction = RecoveryPrediction(
        failure_event_id=event.id,
        model_version="v1",
        feature_snapshot={},
        recovery_probability=0.8
    )
    db_session.add(prediction)
    db_session.commit()

    # Add a completed action so it's included in baseline logic
    from app.models import RecoveryAction
    completed_action = RecoveryAction(
        failure_event_id=event.id,
        action_type="RETRY_LATER",
        status="completed"
    )
    db_session.add(completed_action)
    db_session.commit()

    # Call api_service
    from app.core.api_service import get_dashboard_metrics
    metrics = get_dashboard_metrics(db_session)
    
    # Expect baseline to be simulated deterministically
    # cost of RETRY_LATER is 0.10, but amount_recovered uses amount if success (prob >= 0.5)
    # prob = 0.8 -> success -> amount_recovered = 100.0
    baseline_recovered = metrics["baselineComparison"]["baseline"]["recovered"]
    
    assert baseline_recovered >= 100.0  # it accumulates the DB seeded data as well
    initial_recovered = baseline_recovered
    
    # Change prediction to 0.4
    prediction.recovery_probability = 0.4
    db_session.commit()
    
    metrics = get_dashboard_metrics(db_session)
    baseline_recovered_low = metrics["baselineComparison"]["baseline"]["recovered"]
    
    # prob = 0.4 -> fail -> amount_recovered = 0.0 for this specific payment
    assert baseline_recovered_low == initial_recovered - 100.0
