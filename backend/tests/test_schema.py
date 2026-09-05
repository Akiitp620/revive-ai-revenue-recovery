import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Base, Merchant, Customer, Payment, FailureEvent, RecoveryPrediction,
    RecoveryAction, RecoveryOutcome, EvaluationCase,
    EvaluationResult
)

# Use an in-memory SQLite database for schema testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)


@pytest.fixture(scope="module")
def db():
    # Create the database schema
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop the database schema
        Base.metadata.drop_all(bind=engine)


def test_schema_relationships(db):
    # 1. Create a Merchant
    merchant = Merchant(name="Test Merchant")
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    assert merchant.id is not None

    # 2. Create a Customer
    customer = Customer(merchant_id=merchant.id, external_id="cust_123")
    db.add(customer)
    db.commit()
    db.refresh(customer)
    assert customer.id is not None
    assert customer.merchant.name == "Test Merchant"

    # 3. Create a Payment
    payment = Payment(
        customer_id=customer.id,
        amount=150.0,
        currency="USD",
        status="failed")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    assert payment.customer.external_id == "cust_123"

    # 4. Create a FailureEvent
    failure_event = FailureEvent(
        payment_id=payment.id,
        failure_reason="insufficient_funds",
        context_snapshot={"ip": "127.0.0.1"}
    )
    db.add(failure_event)
    db.commit()
    db.refresh(failure_event)
    assert failure_event.payment.amount == 150.0

    # 5. Create a RecoveryPrediction
    prediction = RecoveryPrediction(
        failure_event_id=failure_event.id,
        model_version="v1.0",
        feature_snapshot={"amount": 150.0, "reason": "insufficient_funds"},
        recovery_probability=0.65
    )
    db.add(prediction)

    # 6. Create a RecoveryAction and Outcome
    action = RecoveryAction(
        failure_event_id=failure_event.id,
        action_type="immediate_retry",
        status="completed"
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    outcome = RecoveryOutcome(
        recovery_action_id=action.id,
        success=True,
        amount_recovered=150.0
    )
    db.add(outcome)

    # 7. Create Evaluation Ground Truth
    eval_case = EvaluationCase(
        failure_event_id=failure_event.id,
        ground_truth_outcome=True,
        ground_truth_amount=150.0
    )
    db.add(eval_case)
    db.commit()

    eval_result = EvaluationResult(
        evaluation_case_id=eval_case.id,
        model_version="v1.0",
        predicted_outcome=True
    )
    db.add(eval_result)
    db.commit()

    # Query relationships to verify
    db.refresh(failure_event)
    assert len(failure_event.predictions) == 1
    assert len(failure_event.actions) == 1
    assert failure_event.actions[0].outcome.success is True
    assert len(failure_event.evaluation_cases) == 1
    assert len(failure_event.evaluation_cases[0].results) == 1

    # Cleanup
    db.query(EvaluationResult).delete()
    db.query(EvaluationCase).delete()
    db.query(RecoveryOutcome).delete()
    db.query(RecoveryAction).delete()
    db.query(RecoveryPrediction).delete()
    db.query(FailureEvent).delete()
    db.query(Payment).delete()
    db.query(Customer).delete()
    db.query(Merchant).delete()
    db.commit()
