from typing import Dict, Any, List


class ActionSimulator:
    """
    Deterministically simulates the outcome of recovery actions
    using synthetic ground-truth data.
    """

    ACTIONS = [
        "RETRY_NOW",
        "RETRY_LATER",
        "ALTERNATE_PAYMENT",
        "REMINDER",
        "HUMAN_REVIEW",
        "STOP"
    ]

    COSTS = {
        "RETRY_NOW": 0.10,
        "RETRY_LATER": 0.10,
        "ALTERNATE_PAYMENT": 0.50,
        "REMINDER": 0.20,
        "HUMAN_REVIEW": 15.00,
        "STOP": 0.00
    }

    def _map_best_action(self, best_action_str: str) -> str:
        """Map the dataset's best_action to our simulator action enum."""
        mapping = {
            "wait_and_retry": "RETRY_LATER",
            "wait_for_paycheck": "RETRY_LATER",
            "stop_and_notify": "STOP",
            "manual_review": "HUMAN_REVIEW",
            "stop": "STOP",
            "immediate_retry": "RETRY_NOW"
        }
        return mapping.get(best_action_str, "STOP")

    def evaluate_action(self, action: str, amount: float,
                        ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single action's expected metrics deterministically.
        """
        is_recoverable = ground_truth.get("recoverable", False)
        true_best_action = self._map_best_action(
            ground_truth.get("best_action", "stop"))

        probability = 0.0

        if is_recoverable:
            if action == true_best_action:
                probability = 0.9  # The best action succeeds 90% of the time
            elif action == "HUMAN_REVIEW":
                probability = 0.95  # Humans can almost always recover if physically possible
            elif action == "ALTERNATE_PAYMENT" and true_best_action in ["RETRY_NOW", "RETRY_LATER"]:
                # Asking for an alternate payment often works if it was a
                # funds/gateway issue
                probability = 0.8
            elif action == "REMINDER" and true_best_action == "RETRY_LATER":
                probability = 0.6  # Reminding works somewhat when waiting for paycheck
            elif action == "RETRY_LATER" and true_best_action == "RETRY_NOW":
                probability = 0.8  # If immediate works, later usually works too
            elif action == "RETRY_NOW" and true_best_action == "RETRY_LATER":
                probability = 0.1  # If we need to wait, retrying now mostly fails

        # Stop always has 0 probability of recovering funds
        if action == "STOP":
            probability = 0.0

        expected_recovery = amount * probability
        cost = self.COSTS.get(action, 0.0)
        expected_net_recovery = expected_recovery - cost

        return {
            "action": action,
            "probability": probability,
            "expected_recovery": expected_recovery,
            "intervention_cost": cost,
            "expected_net_recovery": expected_net_recovery
        }

    def simulate_all_actions(
            self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Produce deterministic outcomes for all permitted actions
        to support counterfactual evaluation.
        """
        amount = event.get("amount", 0.0)

        # Ground truth could be embedded in the event or passed separately
        # (Assuming the event dict from the generator contains these keys)
        ground_truth = {
            "recoverable": event.get("recoverable", False),
            "best_action": event.get("best_action", "stop"),
            "true_root_cause": event.get("true_root_cause", "unknown")
        }

        results = []
        for action in self.ACTIONS:
            metrics = self.evaluate_action(action, amount, ground_truth)
            results.append(metrics)

        return results

    def simulate_operational_outcome(self, action: str, amount: float, prediction) -> Dict[str, Any]:
        """
        Produce a deterministic execution outcome using canonical prediction.
        """
        if not prediction:
            return {"unavailable": True, "reason": "No recovery prediction found"}
            
        base_prob = prediction.recovery_probability
        cost = self.COSTS.get(action, 0.0)
        
        if action == "STOP":
            prob = 0.0
        else:
            prob = base_prob
            if action == "RETRY_NOW":
                prob *= 0.5
            elif action in ["HUMAN_REVIEW", "REVIEW"]:
                prob = min(0.95, prob * 1.5)
            elif action in ["CUSTOMER_REMINDER", "REMINDER"]:
                prob *= 0.7
                
        expected_recovery = amount * prob
        enr = expected_recovery - cost
        
        # Deterministic simulation of boolean success based on probability threshold
        success = prob >= 0.5
        amount_recovered = amount if success else 0.0
        
        return {
            "action": action,
            "probability": prob,
            "expected_recovery": expected_recovery,
            "intervention_cost": cost,
            "expected_net_recovery": enr,
            "success": success,
            "amount_recovered": amount_recovered
        }
