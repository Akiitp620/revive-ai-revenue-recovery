from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class PolicyDecision(BaseModel):
    policy_id: str
    policy_version: str
    rule_matched: str
    final_outcome: str  # "AUTHORIZED", "STOP", "HUMAN_REVIEW", "ESCALATE"
    authorized: bool


class DeterministicPolicyEngine:
    """
    Deterministic rule-based policy engine for authorizing recovery actions.
    No LLM is used here.
    """

    # Constants per requirements
    MAX_RETRIES = 2
    MAX_AUTO_ACTION_VALUE = 50000.0
    HIGH_VALUE_THRESHOLD = 2000.0  # for uncertain evidence

    HARD_DECLINE_ERRORS = {
        "stolen_card", "lost_card", "do_not_honor",
        "fraud_suspected", "R02_account_closed", "R03_no_account"
    }

    def __init__(
            self,
            policy_id: str = "pol_core_1",
            policy_version: str = "v1.0"):
        self.policy_id = policy_id
        self.policy_version = policy_version

    def _decision(
            self,
            rule_matched: str,
            final_outcome: str,
            authorized: bool) -> PolicyDecision:
        return PolicyDecision(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            rule_matched=rule_matched,
            final_outcome=final_outcome,
            authorized=authorized
        )

    def evaluate(self,
                 proposed_action: str,
                 event: Dict[str,
                             Any],
                 expected_net_recovery: float,
                 merchant_allowlist: List[str],
                 min_recovery_threshold: float,
                 evidence_uncertain: bool = False,
                 rag_policy_context: Optional[Dict[str,
                                                   Any]] = None) -> PolicyDecision:
        """
        Evaluate a proposed action against the deterministic policy rules.
        """

        # Optionally override the policy ID/Version using RAG context
        original_policy_id = self.policy_id
        original_policy_version = self.policy_version

        if rag_policy_context:
            self.policy_id = rag_policy_context.get(
                "policy_id", self.policy_id)
            self.policy_version = rag_policy_context.get(
                "policy_version", self.policy_version)

        amount = event.get("amount", 0.0)
        past_attempts = event.get("past_attempts", 0)
        error_code = event.get("error_code", "")

        try:
            # Rule 1: Hard decline -> STOP
            if error_code in self.HARD_DECLINE_ERRORS:
                return self._decision("rule_1_hard_decline", "STOP", False)

            # Rule 2: Max attempts reached -> STOP
            if past_attempts >= self.MAX_RETRIES:
                return self._decision("rule_2_max_attempts", "STOP", False)

            # Rule 4: Exceeds automatic action value -> HUMAN_REVIEW
            if amount >= self.MAX_AUTO_ACTION_VALUE:
                return self._decision(
                    "rule_4_max_auto_value_exceeded", "HUMAN_REVIEW", False)

            # Rule 3: High-value + uncertain evidence -> HUMAN_REVIEW
            if amount >= self.HIGH_VALUE_THRESHOLD and evidence_uncertain:
                return self._decision(
                    "rule_3_high_value_uncertain", "HUMAN_REVIEW", False)

            # Rule 5: Expected net recovery < threshold -> STOP
            if expected_net_recovery < min_recovery_threshold:
                return self._decision(
                    "rule_5_low_expected_value", "STOP", False)

            # Rule 6: Allow only actions present in merchant allowlist
            if proposed_action not in merchant_allowlist:
                # Rule 7: Policy conflicts -> ESCALATE
                return self._decision(
                    "rule_6_action_not_allowed", "ESCALATE", False)

            # Passed all constraints
            return self._decision("rule_default_allow", "AUTHORIZED", True)
        finally:
            # Restore original policy ID/Version
            self.policy_id = original_policy_id
            self.policy_version = original_policy_version
