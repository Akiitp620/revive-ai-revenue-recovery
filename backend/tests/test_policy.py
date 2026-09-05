import pytest
from app.core.policy import DeterministicPolicyEngine


@pytest.fixture
def policy():
    return DeterministicPolicyEngine(
        policy_id="pol_test", policy_version="v1.0")


def test_rule_1_hard_decline(policy):
    event = {"error_code": "lost_card", "amount": 100.0, "past_attempts": 0}
    decision = policy.evaluate(
        "RETRY_LATER",
        event,
        50.0,
        ["RETRY_LATER"],
        10.0)
    assert not decision.authorized
    assert decision.final_outcome == "STOP"
    assert decision.rule_matched == "rule_1_hard_decline"


def test_rule_2_max_attempts(policy):
    event = {
        "error_code": "insufficient_funds",
        "amount": 100.0,
        "past_attempts": 2}  # max attempts is 2
    decision = policy.evaluate(
        "RETRY_LATER",
        event,
        50.0,
        ["RETRY_LATER"],
        10.0)
    assert not decision.authorized
    assert decision.final_outcome == "STOP"
    assert decision.rule_matched == "rule_2_max_attempts"


def test_rule_4_max_auto_value_exceeded(policy):
    event = {
        "error_code": "insufficient_funds",
        "amount": 55000.0,
        "past_attempts": 0}
    decision = policy.evaluate(
        "RETRY_LATER",
        event,
        25000.0,
        ["RETRY_LATER"],
        10.0)
    assert not decision.authorized
    assert decision.final_outcome == "HUMAN_REVIEW"
    assert decision.rule_matched == "rule_4_max_auto_value_exceeded"


def test_rule_3_high_value_uncertain(policy):
    event = {
        "error_code": "insufficient_funds",
        "amount": 2500.0,
        "past_attempts": 0}
    decision = policy.evaluate(
        "RETRY_LATER",
        event,
        2000.0,
        ["RETRY_LATER"],
        10.0,
        evidence_uncertain=True)
    assert not decision.authorized
    assert decision.final_outcome == "HUMAN_REVIEW"
    assert decision.rule_matched == "rule_3_high_value_uncertain"

    # Same value, but certain evidence
    decision_certain = policy.evaluate(
        "RETRY_LATER",
        event,
        2000.0,
        ["RETRY_LATER"],
        10.0,
        evidence_uncertain=False)
    assert decision_certain.authorized
    assert decision_certain.rule_matched == "rule_default_allow"


def test_rule_5_low_expected_value(policy):
    event = {
        "error_code": "insufficient_funds",
        "amount": 100.0,
        "past_attempts": 0}
    # Expected net recovery is 5.0, but threshold is 10.0
    decision = policy.evaluate(
        "RETRY_LATER",
        event,
        5.0,
        ["RETRY_LATER"],
        10.0)
    assert not decision.authorized
    assert decision.final_outcome == "STOP"
    assert decision.rule_matched == "rule_5_low_expected_value"


def test_rule_6_action_not_allowed(policy):
    event = {
        "error_code": "insufficient_funds",
        "amount": 100.0,
        "past_attempts": 0}
    decision = policy.evaluate(
        "ALTERNATE_PAYMENT",
        event,
        50.0,
        ["RETRY_LATER"],
        10.0)
    assert not decision.authorized
    assert decision.final_outcome == "ESCALATE"
    assert decision.rule_matched == "rule_6_action_not_allowed"


def test_default_allow(policy):
    event = {
        "error_code": "insufficient_funds",
        "amount": 100.0,
        "past_attempts": 0}
    decision = policy.evaluate(
        "RETRY_LATER", event, 50.0, [
            "RETRY_LATER", "REMINDER"], 10.0)
    assert decision.authorized
    assert decision.final_outcome == "AUTHORIZED"
    assert decision.rule_matched == "rule_default_allow"
    assert decision.policy_id == "pol_test"
    assert decision.policy_version == "v1.0"
