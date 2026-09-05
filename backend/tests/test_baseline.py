import pytest
from app.core.baseline import BaselinePolicy


@pytest.fixture
def policy():
    return BaselinePolicy()


def test_hard_decline(policy):
    event = {"error_code": "lost_card", "amount": 100.0}
    assert policy.evaluate(event) == "stop_and_notify"


def test_temporary_failure(policy):
    event = {"error_code": "timeout_or_gateway_error", "amount": 50.0}
    assert policy.evaluate(event) == "wait_and_retry"


def test_repeated_failures(policy):
    event = {
        "error_code": "insufficient_funds",
        "past_attempts": 4,
        "amount": 25.0}
    assert policy.evaluate(event) == "stop"


def test_high_value_case(policy):
    event = {
        "error_code": "generic_decline",
        "amount": 3500.0,
        "past_attempts": 0}
    assert policy.evaluate(event) == "manual_review"


def test_simulation(policy):
    # Action matches best_action and is recoverable
    gt = {
        "recoverable": True,
        "best_action": "wait_and_retry",
        "amount_recovered": 50.0}
    success, amount = policy.simulate_outcome("wait_and_retry", gt)
    assert success is True
    assert amount == 50.0

    # Recoverable but action is wrong
    success, amount = policy.simulate_outcome("immediate_retry", gt)
    assert success is False
    assert amount == 0.0

    # Unrecoverable
    gt2 = {
        "recoverable": False,
        "best_action": "stop",
        "amount_recovered": 0.0}
    success, amount = policy.simulate_outcome("stop", gt2)
    assert success is False
    assert amount == 0.0
