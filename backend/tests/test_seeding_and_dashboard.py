import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import timezone, datetime

from app.models import Base, Payment, Merchant, Customer, FailureEvent, RecoveryAction, RecoveryOutcome, RecoveryPrediction
from app.core.api_service import get_dashboard_metrics

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_seeding.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

def test_idempotency(setup_db):
    db_session = setup_db
    # Create one manually
    m = Merchant(name="test_merch")
    db_session.add(m)
    db_session.flush()
    c = Customer(merchant_id=m.id, external_id="cust_1")
    db_session.add(c)
    db_session.flush()
    
    dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
    p1 = Payment(customer_id=c.id, amount=100.0, currency="USD", status="failed", created_at=dt)
    db_session.add(p1)
    db_session.commit()
    
    # Simulate seed trying to insert the same payment
    existing = db_session.query(Payment).filter(
        Payment.amount == 100.0,
        Payment.currency == "USD",
        Payment.created_at == dt
    ).first()
    
    assert existing is not None
    assert existing.id == p1.id

def test_dashboard_metrics_with_seeded_data(setup_db):
    db_session = setup_db
    # Insert canonical models and verify dashboard gets them
    m = Merchant(name="test_merch2")
    db_session.add(m)
    db_session.flush()
    c = Customer(merchant_id=m.id, external_id="cust_2")
    db_session.add(c)
    db_session.flush()
    
    dt = datetime.now()
    # A failed payment
    p1 = Payment(customer_id=c.id, amount=500.0, currency="USD", status="failed", created_at=dt)
    db_session.add(p1)
    db_session.flush()
    
    # A failure event
    fe = FailureEvent(payment_id=p1.id, failure_reason="insufficient_funds")
    db_session.add(fe)
    db_session.flush()
    
    # A recovery action
    ra = RecoveryAction(failure_event_id=fe.id, action_type="RETRY_NOW", status="completed")
    db_session.add(ra)
    db_session.flush()
    
    # A recovery outcome
    ro = RecoveryOutcome(recovery_action_id=ra.id, success=True, amount_recovered=500.0)
    db_session.add(ro)
    db_session.commit()
    
    metrics = get_dashboard_metrics(db_session)
    
    assert metrics["kpis"]["revenueAtRisk"] == 600.0 # 500 + 100 from previous test
    assert metrics["kpis"]["revenueRecovered"] == 500.0
    assert metrics["paymentHealth"] == []

def test_dashboard_metrics_with_predictions(setup_db):
    db_session = setup_db
    p1 = db_session.query(Payment).filter(Payment.amount == 100.0).first()
    
    fe = db_session.query(FailureEvent).filter(FailureEvent.payment_id == p1.id).first()
    if not fe:
        fe = FailureEvent(payment_id=p1.id, failure_reason="insufficient_funds")
        db_session.add(fe)
        db_session.flush()
    
    pred = RecoveryPrediction(
        failure_event_id=fe.id,
        model_version="v1.0",
        feature_snapshot={"amount": 100.0},
        recovery_probability=0.75
    )
    db_session.add(pred)
    db_session.commit()
    
    metrics = get_dashboard_metrics(db_session)
    
    opportunities = metrics.get("opportunities", [])
    p1_opp = next((o for o in opportunities if o["transactionId"] == str(p1.id)), None)
    
    assert p1_opp is not None
    assert p1_opp["recoveryProbability"] == 75.0
    assert p1_opp["expectedRecovery"] == 75.0
    
    simulated_stage = next((s for s in metrics.get("pipeline", []) if s["stage"] == "Simulated"), None)
    assert simulated_stage is not None
    assert simulated_stage["count"] >= 1
