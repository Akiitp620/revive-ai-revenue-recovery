import pytest
import pandas as pd
from pathlib import Path
from app.core.evaluation import (
    compute_all_metrics,
    calculate_recovery_rate,
    calculate_root_cause_accuracy,
    calculate_unnecessary_intervention_rate,
    calculate_escalation_rate,
    calculate_policy_violations,
    calculate_average_decision_latency,
    calculate_tool_success_rate
)

# FIXME: Original 11 tests were accidentally overwritten here. 
# Need to restore original tests if a backup is found.

def test_dataset_splits():
    # Test that splits do not overlap and held-out size is exactly 1500
    data_dir = Path("data/output")
    if not data_dir.exists():
        pytest.skip("Data directory not found. Run dataset generator first.")

    dev_df = pd.read_csv(data_dir / "development.csv")
    val_df = pd.read_csv(data_dir / "validation.csv")
    test_df = pd.read_csv(data_dir / "held_out.csv")

    assert len(test_df) == 1500, "Held-out dataset must be exactly 1500 cases"
    assert len(val_df) == 1500, "Validation dataset must be exactly 1500 cases"
    assert len(dev_df) == 7000, "Development dataset must be exactly 7000 cases"

    # Verify no overlap by payment_id
    dev_ids = set(dev_df["payment_id"].unique())
    val_ids = set(val_df["payment_id"].unique())
    test_ids = set(test_df["payment_id"].unique())

    assert len(dev_ids.intersection(val_ids)) == 0, "Overlap found between dev and val"
    assert len(dev_ids.intersection(test_ids)) == 0, "Overlap found between dev and held-out"
    assert len(val_ids.intersection(test_ids)) == 0, "Overlap found between val and held-out"


def test_core_metric_calculations():
    # Setup simple mock outcomes
    baseline_outcomes = [
        {"amount_recovered": 100.0, "action": "STOP", "best_action": "RETRY_LATER"},
        {"amount_recovered": 0.0, "action": "RETRY_NOW", "best_action": "RETRY_LATER"},
        {"amount_recovered": 50.0, "action": "RETRY_LATER", "best_action": "RETRY_LATER"}
    ]
    
    revive_outcomes = [
        {"amount_recovered": 100.0, "action": "RETRY_LATER", "best_action": "RETRY_LATER", "recoverable": True, "diagnosed_root_cause": "insufficient_funds", "ground_truth_error_code": "insufficient_funds", "final_decision": "EXECUTE", "is_hard_decline": False, "allowlist": ["RETRY_LATER"]},
        {"amount_recovered": 0.0, "action": "STOP", "best_action": "RETRY_LATER", "recoverable": False, "diagnosed_root_cause": "fraud", "ground_truth_error_code": "fraud", "final_decision": "STOP", "is_hard_decline": True, "allowlist": ["RETRY_LATER"]},
        {"amount_recovered": 150.0, "action": "RETRY_LATER", "best_action": "RETRY_LATER", "recoverable": True, "diagnosed_root_cause": "timeout", "ground_truth_error_code": "timeout", "final_decision": "EXECUTE", "is_hard_decline": False, "allowlist": ["RETRY_LATER"]}
    ]
    
    metrics = compute_all_metrics(revive_outcomes, baseline_outcomes, dataset_name="test_split")
    
    assert metrics["dataset_name"] == "test_split"
    assert metrics["sample_count"] == 3
    assert metrics["baseline_recovered_revenue"] == 150.0
    assert metrics["revive_recovered_revenue"] == 250.0
    assert metrics["incremental_recovered_revenue"] == 100.0
    assert metrics["improvement_percentage"] == (100.0 / 150.0) * 100
    
    # Action selection accuracy
    assert metrics["action_selection_accuracy"] == 2/3
    
    # Stop-rule compliance
    assert metrics["stop_rule_compliance"] == 1.0


def test_empty_dataset_safety():
    metrics = compute_all_metrics([], [])
    assert metrics["sample_count"] == 0
    assert metrics["baseline_recovered_revenue"] == 0.0
    assert metrics["revive_recovered_revenue"] == 0.0
    assert metrics["improvement_percentage"] == 0.0
    assert metrics["action_selection_accuracy"] == 0.0
    assert metrics["stop_rule_compliance"] == 1.0


def test_policy_compliance_accounting():
    outcomes = [
        # Allowed action that was executed
        {"action": "RETRY_LATER", "allowlist": ["RETRY_LATER", "STOP"], "final_decision": "EXECUTE"},
        # Not in allowlist, but decision was STOP (not a violation)
        {"action": "RETRY_NOW", "allowlist": ["RETRY_LATER", "STOP"], "final_decision": "STOP"},
        # Not in allowlist, AND executed (violation!)
        {"action": "RETRY_NOW", "allowlist": ["RETRY_LATER", "STOP"], "final_decision": "EXECUTE"},
    ]
    # 1 violation out of 3 = 0.3333
    violations = calculate_policy_violations(outcomes)
    assert abs(violations - (1/3)) < 1e-6

def test_evaluation_failure_accounting():
    # Covers calculate_tool_success_rate
    outcomes = [
        {"tool_calls": 2, "tool_errors": 0},
        {"tool_calls": 3, "tool_errors": 1},
        {"tool_calls": 0, "tool_errors": 0}
    ]
    # Total calls: 5, Total errors: 1
    # Success rate: 1.0 - (1/5) = 0.8
    success_rate = calculate_tool_success_rate(outcomes)
    assert success_rate == 0.8

def test_deterministic_repeated_evaluation():
    baseline_outcomes = [
        {"amount_recovered": 100.0, "action": "STOP", "best_action": "RETRY_LATER"},
    ]
    revive_outcomes = [
        {"amount_recovered": 100.0, "action": "RETRY_LATER", "best_action": "RETRY_LATER", "recoverable": True, "diagnosed_root_cause": "insufficient_funds", "ground_truth_error_code": "insufficient_funds", "final_decision": "EXECUTE", "is_hard_decline": False, "allowlist": ["RETRY_LATER"]},
    ]
    metrics1 = compute_all_metrics(revive_outcomes, baseline_outcomes, dataset_name="deterministic_test")
    metrics2 = compute_all_metrics(revive_outcomes, baseline_outcomes, dataset_name="deterministic_test")
    
    assert metrics1 == metrics2

def test_ground_truth_leakage_prevention():
    # Changing ground_truth_error_code shouldn't affect the amount_recovered in the output metrics
    revive_outcomes = [
        {"amount_recovered": 100.0, "action": "RETRY_LATER", "best_action": "RETRY_LATER", "recoverable": True, "diagnosed_root_cause": "insufficient_funds", "ground_truth_error_code": "insufficient_funds", "final_decision": "EXECUTE", "is_hard_decline": False, "allowlist": ["RETRY_LATER"]},
    ]
    metrics1 = compute_all_metrics(revive_outcomes, [], "leakage_test")
    
    # Mutate ground truth
    revive_outcomes_mutated = [
        {"amount_recovered": 100.0, "action": "RETRY_LATER", "best_action": "RETRY_LATER", "recoverable": True, "diagnosed_root_cause": "insufficient_funds", "ground_truth_error_code": "fraud", "final_decision": "EXECUTE", "is_hard_decline": False, "allowlist": ["RETRY_LATER"]},
    ]
    metrics2 = compute_all_metrics(revive_outcomes_mutated, [], "leakage_test")
    
    assert metrics1["revive_recovered_revenue"] == metrics2["revive_recovered_revenue"]
    # Only root cause accuracy should drop
    assert metrics1["root_cause_accuracy"] == 1.0
    assert metrics2["root_cause_accuracy"] == 0.0

def test_simulator_failure_behavior():
    # Test safe handling when amount_recovered is missing (defaults to 0)
    revive_outcomes = [
        {"action": "RETRY_LATER", "best_action": "RETRY_LATER", "recoverable": True, "diagnosed_root_cause": "insufficient_funds", "ground_truth_error_code": "insufficient_funds", "final_decision": "EXECUTE", "is_hard_decline": False, "allowlist": ["RETRY_LATER"]},
    ]
    metrics = compute_all_metrics(revive_outcomes, [], "failure_test")
    assert metrics["revive_recovered_revenue"] == 0.0
    assert metrics["improvement_percentage"] == 0.0

def test_root_cause_accuracy():
    outcomes = [
        {"diagnosed_root_cause": "fraud", "ground_truth_error_code": "fraud"}, # correct
        {"diagnosed_root_cause": "timeout", "ground_truth_error_code": "insufficient_funds"}, # incorrect
    ]
    acc = calculate_root_cause_accuracy(outcomes)
    assert acc == 0.5

def test_unnecessary_intervention_rate():
    outcomes = [
        {"recoverable": False, "action": "STOP"}, # correct (no intervention)
        {"recoverable": False, "action": "RETRY_NOW"}, # unnecessary intervention!
        {"recoverable": True, "action": "RETRY_NOW"}, # not counted (recoverable)
    ]
    rate = calculate_unnecessary_intervention_rate(outcomes)
    assert rate == 0.5 # 1 unnecessary out of 2 unrecoverable

def test_escalation_rate():
    outcomes = [
        {"final_decision": "EXECUTE"},
        {"final_decision": "STOP"},
        {"final_decision": "REVIEW"},
        {"final_decision": "ESCALATE"},
        {"final_decision": "HUMAN_REVIEW"}
    ]
    rate = calculate_escalation_rate(outcomes)
    # 3 escalations out of 5 = 0.6
    assert rate == 0.6
