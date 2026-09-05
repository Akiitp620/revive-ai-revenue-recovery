import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.models import Base, Payment, Customer, Merchant, FailureEvent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

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
    db = TestingSessionLocal()
    merchant = Merchant(name="Test Merchant")
    db.add(merchant)
    db.commit()
    customer = Customer(merchant_id=merchant.id, external_id="ext_cust_sse")
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
    db.close()

    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_sse_investigation_stream(monkeypatch):
    def mock_get_payment(pid):
        return {"payment_id": pid, "amount": 100.0, "status": "failed", "currency": "USD"}
    monkeypatch.setattr("app.core.agent_tools.get_payment", mock_get_payment)
    
    # 1. Non-existent investigation
    resp = client.get("/api/v1/investigations/not_found/stream")
    assert resp.status_code == 404

    # 2. Completed investigation
    resp = client.post("/api/v1/investigations", json={"payment_id": "1"})
    assert resp.status_code == 200
    investigation_id = resp.json()["investigation_id"]

    # Call the stream endpoint
    stream_resp = client.get(
        f"/api/v1/investigations/{investigation_id}/stream")
    assert stream_resp.status_code == 200
    assert stream_resp.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Read events
    lines = stream_resp.text.strip().split("\n\n")
    events = []
    for line in lines:
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    assert len(events) > 0
    event_types = [e["event_type"] for e in events]

    # Ensure ordered correctly
    assert event_types[0] == "REVENUE_RISK_DETECTED"

    assert event_types[-1] in ["ACTION_SELECTED",
                               "HUMAN_REVIEW_REQUESTED",
                               "PAYMENT_NOT_RECOVERED",
                               "FALLBACK_APPLIED"]
