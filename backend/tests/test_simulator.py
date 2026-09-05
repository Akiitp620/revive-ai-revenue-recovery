import pytest
from app.core.simulator import ActionSimulator


@pytest.fixture
def simulator():
    return ActionSimulator()


def test_retry_now_action(simulator):
    event = {
        "amount": 100.0,
        "recoverable": True,
        "best_action": "immediate_retry"
    }
    results = simulator.simulate_all_actions(event)
    retry_now = next(r for r in results if r["action"] == "RETRY_NOW")

    assert retry_now["probability"] == 0.9
    assert retry_now["expected_recovery"] == 90.0
    assert retry_now["intervention_cost"] == 0.10
    assert retry_now["expected_net_recovery"] == 89.90


def test_retry_later_action(simulator):
    event = {
        "amount": 50.0,
        "recoverable": True,
        "best_action": "wait_and_retry"
    }
    results = simulator.simulate_all_actions(event)
    retry_later = next(r for r in results if r["action"] == "RETRY_LATER")

    assert retry_later["probability"] == 0.9
    assert retry_later["expected_recovery"] == 45.0
    assert retry_later["intervention_cost"] == 0.10
    assert retry_later["expected_net_recovery"] == 44.90


def test_alternate_payment_action(simulator):
    event = {
        "amount": 200.0,
        "recoverable": True,
        "best_action": "wait_and_retry"
    }
    results = simulator.simulate_all_actions(event)
    alt_payment = next(
        r for r in results if r["action"] == "ALTERNATE_PAYMENT")

    # 0.8 prob if best is wait_and_retry
    assert alt_payment["probability"] == 0.8
    assert alt_payment["expected_recovery"] == 160.0
    assert alt_payment["intervention_cost"] == 0.50
    assert alt_payment["expected_net_recovery"] == 159.50


def test_reminder_action(simulator):
    event = {
        "amount": 100.0,
        "recoverable": True,
        "best_action": "wait_for_paycheck"  # maps to RETRY_LATER
    }
    results = simulator.simulate_all_actions(event)
    reminder = next(r for r in results if r["action"] == "REMINDER")

    # 0.6 prob if best is wait_for_paycheck
    assert reminder["probability"] == 0.6
    assert reminder["expected_recovery"] == 60.0
    assert reminder["intervention_cost"] == 0.20
    assert reminder["expected_net_recovery"] == 59.80


def test_human_review_action(simulator):
    event = {
        "amount": 5000.0,
        "recoverable": True,
        "best_action": "manual_review"
    }
    results = simulator.simulate_all_actions(event)
    human_review = next(r for r in results if r["action"] == "HUMAN_REVIEW")

    assert human_review["probability"] == 0.9
    assert human_review["expected_recovery"] == 4500.0
    assert human_review["intervention_cost"] == 15.00
    assert human_review["expected_net_recovery"] == 4485.00

    # Even if true_best is immediate_retry, human can still recover
    event2 = {
        "amount": 100.0,
        "recoverable": True,
        "best_action": "immediate_retry"}
    res2 = simulator.simulate_all_actions(event2)
    hr2 = next(r for r in res2 if r["action"] == "HUMAN_REVIEW")
    assert hr2["probability"] == 0.95


def test_stop_action(simulator):
    event = {
        "amount": 100.0,
        "recoverable": False,
        "best_action": "stop_and_notify"
    }
    results = simulator.simulate_all_actions(event)
    stop = next(r for r in results if r["action"] == "STOP")

    assert stop["probability"] == 0.0
    assert stop["expected_recovery"] == 0.0
    assert stop["intervention_cost"] == 0.0
    assert stop["expected_net_recovery"] == 0.0

    # Everything should have 0 prob since recoverable is False
    for r in results:
        assert r["probability"] == 0.0
        assert r["expected_recovery"] == 0.0
