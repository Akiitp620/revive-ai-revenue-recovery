import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Base, Payment, Customer, Merchant, FailureEvent, AuditLog, PaymentAttempt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    # Seed data
    db = TestingSessionLocal()
    merchant = Merchant(name="Test Merchant")
    db.add(merchant)
    db.commit()

    customer = Customer(merchant_id=merchant.id, external_id="ext_cust_1")
    db.add(customer)
    db.commit()

    payment = Payment(
        customer_id=customer.id,
        amount=100.0,
        currency="USD",
        status="failed")
    db.add(payment)
    db.commit()

    failure = FailureEvent(
        payment_id=payment.id,
        failure_reason="insufficient_funds")
    db.add(failure)
    db.commit()

    from app.models import RecoveryPrediction
    prediction = RecoveryPrediction(
        failure_event_id=failure.id,
        model_version="v1",
        feature_snapshot={},
        recovery_probability=0.8
    )
    db.add(prediction)
    db.commit()

    attempt = PaymentAttempt(
        payment_id=payment.id,
        status="failed",
        error_code="insufficient_funds")
    db.add(attempt)
    db.commit()

    db.close()

    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_payment_retrieval():
    assert AuditLog is not None
    # Insert a dummy payment directly into the test DB("/api/v1/payments")
    response = client.get("/api/v1/payments")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    payment_id = data["items"][0]["id"]

    # Detail retrieval
    response = client.get(f"/api/v1/payments/{payment_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["amount"] == 100.0
    assert detail["status"] == "failed"


def test_investigation_creation_and_audit():
    # 1. Create Investigation
    # In the seeded DB, payment ID is 1
    payment_id_str = "pay_1"

    # Our DB seed uses standard ID 1, but the agent mock tools from before might use string IDs.
    # We will just pass "1" as a string to match the mocked agent_tools if we rely on it,
    # or the DB id. Wait, the API service uses the mocked FakeLLM but the tools might actually try to fetch from DB if they were hooked up.
    # Currently agent_tools are hardcoded placeholders in the prototype.
    response = client.post("/api/v1/investigations", json={"payment_id": "1"})
    assert response.status_code == 200
    data = response.json()
    assert "investigation_id" in data
    assert data["recommendation"] in ["RETRY_LATER", "REVIEW"]
    assert data["final_decision"] in [
        "EXECUTE", "ESCALATE", "REVIEW", "RETRY_LATER"]

    investigation_id = data["investigation_id"]

    # 2. Get Audit Trail
    response = client.get(f"/api/v1/audit/{investigation_id}")
    assert response.status_code == 200
    audit_data = response.json()

    assert audit_data["investigation_id"] == investigation_id
    events = audit_data["events"]
    assert len(events) > 0
    event_types = [e["event_type"] for e in events]
    assert "REVENUE_RISK_DETECTED" in event_types
    assert "HUMAN_REVIEW_REQUESTED" in event_types or "ACTION_SELECTED" in event_types

    for event in events:
        if event["event_type"] == "ACTION_SELECTED":
            assert "strategy" in event["metadata_snapshot"]
        elif event["event_type"] == "HUMAN_REVIEW_REQUESTED":
            assert "reason" in event["metadata_snapshot"]


def test_recovery_options():
    response = client.get("/api/v1/recovery/options/1")
    assert response.status_code == 200
    data = response.json()
    assert "allowed_actions" in data
    assert "RETRY_LATER" in data["allowed_actions"]


def test_execution_policy():
    response = client.post("/api/v1/recovery/execute", json={
        "payment_id": "1",
        "action": "RETRY_LATER"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
