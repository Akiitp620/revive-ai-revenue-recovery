import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, AuditLog
from app.core.audit import InvestigationAuditService

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
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_investigation_audit_append_only_and_no_cot(db):
    assert AuditLog is not None
    service = InvestigationAuditService(db)

    # Simulate agent generating a chain of thought along with normal output
    metadata_with_cot = {
        "reasoning": "I should retry because the amount is low.",
        "thought": "Maybe it will work.",
        "strategy": "RETRY_LATER",
        "model_version": "v1.2",
        "policy_version": "2.0"
    }

    service.log_event(
        trace_id="tr_123",
        investigation_id="inv_999",
        payment_id="pay_456",
        actor="ReviveAgent",
        event_type="ACTION_SELECTED",
        metadata=metadata_with_cot
    )

    logs = service.get_investigation_history("inv_999")
    assert len(logs) == 1

    logged_event = logs[0]
    assert logged_event.trace_id == "tr_123"
    assert logged_event.investigation_id == "inv_999"
    assert logged_event.actor == "ReviveAgent"
    assert logged_event.event_type == "ACTION_SELECTED"

    # Verify chain-of-thought fields were stripped
    assert "reasoning" not in logged_event.metadata_snapshot
    assert "thought" not in logged_event.metadata_snapshot

    # Verify valid metadata remains
    assert logged_event.metadata_snapshot["strategy"] == "RETRY_LATER"
    assert logged_event.metadata_snapshot["model_version"] == "v1.2"
    assert logged_event.metadata_snapshot["policy_version"] == "2.0"


def test_investigation_audit_chronological_order(db):
    service = InvestigationAuditService(db)

    # We add another event for the same investigation
    service.log_event(
        trace_id="tr_123",
        investigation_id="inv_999",
        payment_id="pay_456",
        actor="DeterministicPolicyEngine",
        event_type="POLICY_VALIDATED",
        metadata={"rule": "allow_retry"}
    )

    logs = service.get_investigation_history("inv_999")
    assert len(logs) == 2

    assert logs[0].event_type == "ACTION_SELECTED"
    assert logs[1].event_type == "POLICY_VALIDATED"

    # Verify different investigation ID doesn't show up here
    service.log_event(
        trace_id="tr_444",
        investigation_id="inv_888",
        payment_id="pay_111",
        actor="ReviveAgent",
        event_type="FAILURE_CONTEXT_LOADED",
        metadata={}
    )

    logs_888 = service.get_investigation_history("inv_888")
    assert len(logs_888) == 1
    assert logs_888[0].investigation_id == "inv_888"
