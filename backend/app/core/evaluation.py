from typing import List, Dict, Any, Union


def calculate_incremental_revenue(
        revive_outcomes: List[Dict[str, Any]], baseline_outcomes: List[Dict[str, Any]]) -> float:
    revive_sum = sum(outcome.get("amount_recovered", 0.0)
                     for outcome in revive_outcomes)
    baseline_sum = sum(outcome.get("amount_recovered", 0.0)
                       for outcome in baseline_outcomes)
    return revive_sum - baseline_sum


def calculate_recovery_rate(outcomes: List[Dict[str, Any]]) -> float:
    if not outcomes:
        return 0.0
    recovered_count = sum(
        1 for o in outcomes if o.get(
            "amount_recovered", 0.0) > 0)
    return recovered_count / len(outcomes)


def calculate_action_selection_accuracy(
        outcomes: List[Dict[str, Any]]) -> float:
    if not outcomes:
        return 0.0
    correct = sum(1 for o in outcomes if o.get(
        "action") == o.get("best_action"))
    return correct / len(outcomes)


def calculate_root_cause_accuracy(outcomes: List[Dict[str, Any]]) -> float:
    if not outcomes:
        return 0.0
    correct = sum(1 for o in outcomes if o.get(
        "diagnosed_root_cause") == o.get("ground_truth_error_code"))
    return correct / len(outcomes)


def calculate_unnecessary_intervention_rate(
        outcomes: List[Dict[str, Any]]) -> float:
    unrecoverable = [o for o in outcomes if not o.get("recoverable", False)]
    if not unrecoverable:
        return 0.0
    # Any action other than STOP on an unrecoverable case is an unnecessary
    # intervention
    interventions = sum(1 for o in unrecoverable if o.get("action") != "STOP")
    return interventions / len(unrecoverable)


def calculate_escalation_rate(outcomes: List[Dict[str, Any]]) -> float:
    if not outcomes:
        return 0.0
    escalations = sum(
        1 for o in outcomes if o.get("final_decision") in [
            "REVIEW", "ESCALATE", "HUMAN_REVIEW"])
    return escalations / len(outcomes)


def calculate_stop_rule_compliance(outcomes: List[Dict[str, Any]]) -> float:
    hard_declines = [o for o in outcomes if o.get("is_hard_decline", False)]
    if not hard_declines:
        return 1.0
    compliant = sum(1 for o in hard_declines if o.get(
        "final_decision") == "STOP")
    return compliant / len(hard_declines)


def calculate_policy_violations(outcomes: List[Dict[str, Any]]) -> float:
    if not outcomes:
        return 0.0
    # Violation if action is not in allowlist AND it was executed
    violations = sum(
        1 for o in outcomes
        if o.get("action") not in o.get("allowlist", [])
        and o.get("final_decision") == "EXECUTE"
    )
    return violations / len(outcomes)


def calculate_average_decision_latency(
        outcomes: List[Dict[str, Any]]) -> float:
    if not outcomes:
        return 0.0
    total_time = sum(o.get("latency", 0.0) for o in outcomes)
    return total_time / len(outcomes)


def calculate_tool_success_rate(outcomes: List[Dict[str, Any]]) -> float:
    total_tools = sum(o.get("tool_calls", 0) for o in outcomes)
    total_errors = sum(o.get("tool_errors", 0) for o in outcomes)

    if total_tools == 0:
        return 1.0

    return max(0.0, 1.0 - (total_errors / total_tools))


def compute_all_metrics(revive_outcomes: List[Dict[str, Any]],
                        baseline_outcomes: List[Dict[str, Any]],
                        dataset_name: str = "held_out") -> Dict[str, Union[float, int, str]]:
    
    revive_revenue = sum(o.get("amount_recovered", 0.0) for o in revive_outcomes)
    baseline_revenue = sum(o.get("amount_recovered", 0.0) for o in baseline_outcomes)
    incremental = revive_revenue - baseline_revenue
    improvement_percentage = (incremental / baseline_revenue * 100) if baseline_revenue > 0 else 0.0

    return {
        "dataset_name": dataset_name,
        "sample_count": len(revive_outcomes),
        "baseline_recovered_revenue": baseline_revenue,
        "revive_recovered_revenue": revive_revenue,
        "incremental_recovered_revenue": incremental,
        "improvement_percentage": improvement_percentage,
        "recovery_rate": calculate_recovery_rate(revive_outcomes),
        "action_selection_accuracy": calculate_action_selection_accuracy(revive_outcomes),
        "root_cause_accuracy": calculate_root_cause_accuracy(revive_outcomes),
        "unnecessary_intervention_rate": calculate_unnecessary_intervention_rate(revive_outcomes),
        "escalation_rate": calculate_escalation_rate(revive_outcomes),
        "stop_rule_compliance": calculate_stop_rule_compliance(revive_outcomes),
        "policy_violations": calculate_policy_violations(revive_outcomes),
        "average_decision_latency": calculate_average_decision_latency(revive_outcomes),
        "tool_success_rate": calculate_tool_success_rate(revive_outcomes),
    }
