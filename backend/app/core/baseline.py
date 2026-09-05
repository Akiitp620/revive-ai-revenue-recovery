from typing import Dict, Any, Tuple


class BaselinePolicy:
    """
    A purely deterministic, rule-based baseline policy for revenue recovery.
    Exists only to provide a benchmark for ML/AI approaches.
    """

    HARD_DECLINE_ERRORS = {
        "stolen_card", "lost_card", "do_not_honor",
        "fraud_suspected", "R02_account_closed", "R03_no_account"
    }

    def evaluate(self, event: Dict[str, Any]) -> str:
        """
        Determines the baseline action based on simple rules.
        """
        error_code = event.get("error_code")
        past_attempts = event.get("past_attempts", 0)
        amount = event.get("amount", 0.0)

        if error_code in self.HARD_DECLINE_ERRORS:
            return "stop_and_notify"

        if past_attempts >= 3:
            return "stop"

        if amount >= 2000.0:
            return "manual_review"

        if error_code == "timeout_or_gateway_error":
            return "wait_and_retry"

        if error_code == "insufficient_funds":
            return "wait_for_paycheck"

        # Default fallback
        return "immediate_retry"

    def simulate_outcome(self, baseline_action: str,
                         ground_truth: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Simulate the outcome of the baseline action against the ground truth.
        """
        is_recoverable = ground_truth.get("recoverable", False)
        best_action = ground_truth.get("best_action")

        # In a real system, multiple actions might work (e.g. wait_and_retry might eventually
        # work instead of wait_for_paycheck). But for strict baseline simulation against this
        # prototype dataset, we expect an exact match or a generalized fallback
        # success.

        # Simplified simulator rules:
        if not is_recoverable:
            return False, 0.0

        if baseline_action == best_action:
            return True, float(ground_truth.get("amount_recovered", 0.0))

        # If recoverable but action was wrong (e.g. immediate retry on
        # insufficient funds)
        return False, 0.0
