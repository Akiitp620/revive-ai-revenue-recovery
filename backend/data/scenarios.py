import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

class ScenarioGenerator:
    def __init__(self, fake):
        self.fake = fake
        
    def base_event(self) -> Dict[str, Any]:
        """Generate common baseline fields for any payment event."""
        event_time = self.fake.date_time_between(start_date="-1y", end_date="now")
        return {
            "payment_id": self.fake.uuid4(),
            "customer_id": self.fake.uuid4(),
            "merchant_id": f"merch_{random.randint(1, 100)}",
            "amount": round(np.random.lognormal(mean=3.5, sigma=1.2), 2),
            "currency": "USD",
            "payment_method": random.choice(["card", "ach", "wallet"]),
            "processor": random.choice(["stripe", "adyen", "braintree"]),
            "timestamp": event_time,
            "device_type": random.choice(["mobile", "desktop", "unknown"]),
            "country": self.fake.country_code()
        }

    def s1_temporary_degradation(self) -> Dict[str, Any]:
        """
        Temporary degradation: Clusters by time/bank/method. Highly recoverable via wait.
        """
        event = self.base_event()
        # Override to create clustering effect
        event["processor"] = "stripe"
        event["payment_method"] = "card"
        event["bank"] = random.choice(["BankA", "BankB"])
        event["error_code"] = "timeout_or_gateway_error"
        event["past_attempts"] = 0
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": "gateway_timeout",
                "recoverable": True,
                "best_action": "wait_and_retry",
                "eventual_outcome": True,
                "amount_recovered": event["amount"]
            }
        }

    def s2_insufficient_funds(self) -> Dict[str, Any]:
        """
        Insufficient funds: Usually recoverable on payday, smaller amounts easier.
        """
        event = self.base_event()
        event["error_code"] = "insufficient_funds"
        event["past_attempts"] = random.randint(0, 1)
        
        # Lower amount = higher chance of recovery
        recoverable = event["amount"] < 100 or random.random() < 0.3
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": "insufficient_funds",
                "recoverable": recoverable,
                "best_action": "wait_for_paycheck" if recoverable else "manual_review",
                "eventual_outcome": recoverable,
                "amount_recovered": event["amount"] if recoverable else 0.0
            }
        }

    def s3_hard_decline(self) -> Dict[str, Any]:
        """
        Hard decline: Repeated failure patterns (stolen/lost/do_not_honor). Never recoverable automatically.
        """
        event = self.base_event()
        event["error_code"] = random.choice(["stolen_card", "lost_card", "do_not_honor", "fraud_suspected"])
        event["past_attempts"] = random.randint(1, 3) # often tried already
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": event["error_code"],
                "recoverable": False,
                "best_action": "stop_and_notify",
                "eventual_outcome": False,
                "amount_recovered": 0.0
            }
        }

    def s4_high_value_uncertain(self) -> Dict[str, Any]:
        """
        High-value uncertain: High exposure, incomplete evidence. Needs manual review.
        """
        event = self.base_event()
        event["amount"] = round(random.uniform(2000.0, 15000.0), 2)
        event["error_code"] = "generic_decline"
        event["past_attempts"] = 0
        event["device_type"] = "unknown"
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": "risk_block_or_limit",
                "recoverable": random.random() < 0.5, # 50/50 chance if contacted
                "best_action": "manual_review",
                "eventual_outcome": False, # automation should not recover this
                "amount_recovered": 0.0
            }
        }

    def s5_method_specific_issue(self) -> Dict[str, Any]:
        """
        Method-specific: e.g. ACH returns (R01, R02). Distinct error codes, delayed failure.
        """
        event = self.base_event()
        event["payment_method"] = "ach"
        event["error_code"] = random.choice(["R01_nsf", "R02_account_closed", "R03_no_account"])
        event["past_attempts"] = 0
        
        is_nsf = event["error_code"] == "R01_nsf"
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": event["error_code"],
                "recoverable": is_nsf,
                "best_action": "wait_and_retry" if is_nsf else "stop",
                "eventual_outcome": is_nsf,
                "amount_recovered": event["amount"] if is_nsf else 0.0
            }
        }

    def s6_repeated_recovery_failure(self) -> Dict[str, Any]:
        """
        Repeated failure: Diminishing value. High past attempts, low chance of recovery.
        """
        event = self.base_event()
        event["error_code"] = random.choice(["insufficient_funds", "generic_decline"])
        event["past_attempts"] = random.randint(3, 7)
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": "chronic_failure",
                "recoverable": False,
                "best_action": "stop",
                "eventual_outcome": False,
                "amount_recovered": 0.0
            }
        }

    def s7_unknown_failure(self) -> Dict[str, Any]:
        """
        Unknown failure: Lack of evidence, blank error codes or random stuff.
        """
        event = self.base_event()
        event["error_code"] = random.choice(["", "unknown", "system_error", None])
        event["past_attempts"] = 0
        
        recoverable = random.random() < 0.2
        
        return {
            "input": event,
            "ground_truth": {
                "true_root_cause": "unclassified",
                "recoverable": recoverable,
                "best_action": "immediate_retry" if recoverable else "manual_review",
                "eventual_outcome": recoverable,
                "amount_recovered": event["amount"] if recoverable else 0.0
            }
        }
