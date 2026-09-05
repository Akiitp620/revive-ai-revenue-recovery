import time
import uuid
from typing import Dict, Any, List, TypedDict, Optional
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseChatModel

# Assuming we have our previously built policy engine
from app.core.policy import DeterministicPolicyEngine
from app.core import agent_tools
from app.core.rag import PolicyRAG

# Assume AuditService interface


class DummyAuditService:
    def log_event(
            self,
            trace_id,
            investigation_id,
            payment_id,
            actor,
            event_type,
            metadata):
        pass

# State definition


class InvestigationState(TypedDict):
    trace_id: str
    investigation_id: str
    payment_id: str
    recovery_score: float
    failure_context: Dict[str, Any]
    customer_context: Dict[str, Any]
    policy_context: Dict[str, Any]
    rag_policy_context: Optional[Dict[str, Any]]
    counterfactual_outcomes: Dict[str, Any]
    candidate_actions: List[str]
    supporting_evidence: List[str]
    missing_evidence: List[str]
    recommendation: str
    confidence: float
    final_decision: str
    tool_calls: int
    errors: List[str]
    timestamps: Dict[str, float]


class AgentRecommendation(BaseModel):
    strategy: str = Field(
        description="The recommended recovery strategy action, e.g., RETRY_LATER, STOP")
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0")
    supporting_evidence: List[str] = Field(
        description="List of concise decision factors")
    missing_evidence: List[str] = Field(
        description="List of unavailable context or evidence")
    root_cause: str = Field(default="UNKNOWN",
                            description="Diagnosed root cause for failure")


class ReviveAgent:
    def __init__(
            self,
            llm: BaseChatModel,
            policy_engine: Optional[DeterministicPolicyEngine] = None,
            policy_rag: Optional[PolicyRAG] = None,
            audit_service=None):
        self.llm = llm
        self.policy_engine = policy_engine or DeterministicPolicyEngine()
        self.policy_rag = policy_rag
        self.audit_service = audit_service or DummyAuditService()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(InvestigationState)

        # Add nodes
        workflow.add_node("load_payment", self.load_payment)
        workflow.add_node("diagnose", self.diagnose)
        workflow.add_node("check_context", self.check_context)
        workflow.add_node("generate_actions", self.generate_actions)
        workflow.add_node("simulate", self.simulate)
        workflow.add_node("recommend", self.recommend)
        workflow.add_node("policy_validate", self.policy_validate)
        workflow.add_node("execute_or_review", self.execute_or_review)
        workflow.add_node("record_outcome", self.record_outcome)

        # Build edges linearly per requirements
        workflow.set_entry_point("load_payment")
        workflow.add_edge("load_payment", "diagnose")
        workflow.add_edge("diagnose", "check_context")
        workflow.add_edge("check_context", "generate_actions")
        workflow.add_edge("generate_actions", "simulate")
        workflow.add_edge("simulate", "recommend")
        workflow.add_edge("recommend", "policy_validate")
        workflow.add_edge("policy_validate", "execute_or_review")
        workflow.add_edge("execute_or_review", "record_outcome")
        workflow.add_edge("record_outcome", END)

        return workflow.compile()

    # Node Implementations
    def load_payment(self, state: InvestigationState) -> Dict[str, Any]:
        """Load initial payment and basic info."""
        ts = state.get("timestamps", {})
        ts["start"] = time.time()

        self.audit_service.log_event(
            trace_id=state["trace_id"],
            investigation_id=state["investigation_id"],
            payment_id=state["payment_id"],
            actor="ReviveAgent",
            event_type="REVENUE_RISK_DETECTED",
            metadata={"source": "system"}
        )

        try:
            payment = agent_tools.get_payment(state["payment_id"])

            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="FAILURE_CONTEXT_LOADED",
                metadata={"payment_amount": payment.get("amount")}
            )
            return {
                "failure_context": payment,
                "tool_calls": state.get(
                    "tool_calls",
                    0) + 1,
                "timestamps": ts}
        except Exception as e:
            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="TOOL_FAILED",
                metadata={"error": str(e)}
            )
            return {"failure_context": {}, "errors": state.get(
                "errors", []) + [str(e)], "timestamps": ts}

    def diagnose(self, state: InvestigationState) -> Dict[str, Any]:
        """Inspect failure context and attempts."""
        try:
            fc = agent_tools.get_failure_context(state["payment_id"])
            attempts = agent_tools.get_payment_attempts(state["payment_id"])
            merged_fc = {**state.get("failure_context", {}),
                         **fc, "attempts": attempts}
            return {
                "failure_context": merged_fc,
                "tool_calls": state.get(
                    "tool_calls",
                    0) + 2}
        except Exception as e:
            return {"errors": state.get("errors", []) + [str(e)]}

    def check_context(self, state: InvestigationState) -> Dict[str, Any]:
        """Inspect customer and merchant context."""
        try:
            cust = agent_tools.get_customer_history(state["payment_id"])
            policy = agent_tools.get_merchant_policy("merch_default")

            missing = state.get("missing_evidence", [])
            if not cust:
                missing = missing + ["customer_history"]

            tool_calls = state.get("tool_calls", 0) + 2
            rag_context = None

            if self.policy_rag:
                fc = state.get("failure_context", {})
                error = fc.get("error_code", "")
                amount = fc.get("amount", 0.0)
                query = f"What merchant policy applies to this recovery decision? Error code: {error}. Amount: {amount}."
                rag_results = self.policy_rag.retrieve_policy(query)
                tool_calls += 1
                if rag_results:
                    rag_context = rag_results[0]

            return {
                "customer_context": cust,
                "policy_context": policy,
                "rag_policy_context": rag_context,
                "missing_evidence": missing,
                "tool_calls": tool_calls
            }
        except Exception as e:
            return {"errors": state.get("errors", []) +
                    [str(e)], "missing_evidence": state.get("missing_evidence", []) +
                    ["customer_history", "merchant_policy"]}

    def generate_actions(self, state: InvestigationState) -> Dict[str, Any]:
        """Generate candidate actions."""
        policy = state.get("policy_context", {})
        candidates = policy.get("allowlist", ["STOP"])
        return {"candidate_actions": candidates}

    def simulate(self, state: InvestigationState) -> Dict[str, Any]:
        """Simulate all actions for UI presentation and counterfactual analysis."""
        try:
            outcomes = {}
            from app.core.simulator import ActionSimulator
            for action in ActionSimulator.ACTIONS:
                outcomes[action] = agent_tools.simulate_recovery_action(
                    action, state["payment_id"])

            # Use the recommended/default action's probability as the main score
            sim = outcomes.get("RETRY_LATER", {})
            if not sim and outcomes:
                sim = list(outcomes.values())[0]

            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="RECOVERY_OPTIONS_SIMULATED",
                metadata={
                    "simulated_probability": sim.get("probability", 0.0),
                    "counterfactuals": outcomes
                }
            )
            return {
                "recovery_score": sim.get(
                    "probability",
                    0.85),
                "counterfactual_outcomes": outcomes,
                "tool_calls": state.get(
                    "tool_calls",
                    0) + 1}
        except Exception as e:
            return {"errors": state.get("errors", []) + [str(e)]}

    def recommend(self, state: InvestigationState) -> Dict[str, Any]:
        """Recommend strategy using deterministic selection + LLM explanation."""
        if state.get("tool_calls", 0) > 10:
            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="FALLBACK_APPLIED",
                metadata={"reason": "tool_calls_exceeded"}
            )
            return {
                "recommendation": "REVIEW",
                "confidence": 0.0,
                "final_decision": "REVIEW"}

        if state.get("errors"):
            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="FALLBACK_APPLIED",
                metadata={"reason": "errors_present"}
            )
            return {
                "recommendation": "REVIEW",
                "confidence": 0.0,
                "final_decision": "REVIEW"}

        candidates = state.get("candidate_actions", [])
        outcomes = state.get("counterfactual_outcomes", {})
        
        # Deterministic selection
        best_action = "REVIEW"
        best_enr = -float('inf')
        for action in candidates:
            if action in outcomes:
                enr = outcomes[action].get("expected_net_recovery", -float('inf'))
                if enr > best_enr:
                    best_enr = enr
                    best_action = action

        prompt = (
            f"Analyze recovery for payment {state['payment_id']}.\n"
            f"Failure Context: {state.get('failure_context')}\n"
            f"Customer: {state.get('customer_context')}\n"
            f"Candidates: {state.get('candidate_actions')}\n"
            f"Missing: {state.get('missing_evidence')}\n"
            f"RAG Policy Context: {state.get('rag_policy_context')}\n"
            f"The deterministic engine selected action '{best_action}'. "
            "Provide a concise diagnosis and supporting evidence explaining why this is appropriate. "
            "Set strategy to the selected action."
        )

        try:
            llm_with_struct = self.llm.with_structured_output(
                AgentRecommendation)
            result = llm_with_struct.invoke(prompt)

            missing = list(
                set(state.get("missing_evidence", []) + result.missing_evidence))
                
            # OVERRIDE the LLM's selected strategy with our deterministic one
            final_strategy = best_action

            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="ACTION_SELECTED",
                metadata={
                    "strategy": final_strategy,
                    "confidence": result.confidence})

            if result.confidence < 0.5:
                return {
                    "recommendation": "REVIEW",
                    "confidence": result.confidence,
                    "supporting_evidence": result.supporting_evidence,
                    "missing_evidence": missing
                }

            return {
                "recommendation": final_strategy,
                "confidence": result.confidence,
                "supporting_evidence": result.supporting_evidence,
                "missing_evidence": missing
            }
        except Exception as e:
            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="TOOL_FAILED",
                metadata={"error": "llm_invocation_failed"}
            )
            return {"errors": state.get("errors",
                                        []) + [str(e)],
                    "recommendation": "REVIEW",
                    "confidence": 0.0}

    def policy_validate(self, state: InvestigationState) -> Dict[str, Any]:
        """Validate recommendation against deterministic policy."""
        rec = state.get("recommendation", "STOP")

        if rec == "REVIEW":
            self.audit_service.log_event(
                trace_id=state["trace_id"],
                investigation_id=state["investigation_id"],
                payment_id=state["payment_id"],
                actor="ReviveAgent",
                event_type="HUMAN_REVIEW_REQUESTED",
                metadata={"reason": "confidence_or_fallback"}
            )
            return {"final_decision": "REVIEW"}

        fc = state.get("failure_context", {})
        event = {
            "amount": fc.get("amount", 0.0),
            "past_attempts": len(fc.get("attempts", [])),
            "error_code": fc.get("error_code", "")
        }

        allowlist = state.get("policy_context", {}).get("allowlist", [])
        min_thresh = state.get(
            "policy_context", {}).get(
            "min_recovery_threshold", 0.0)

        enr = event["amount"] * state.get("recovery_score", 0.0)

        decision = self.policy_engine.evaluate(
            proposed_action=rec,
            event=event,
            expected_net_recovery=enr,
            merchant_allowlist=allowlist,
            min_recovery_threshold=min_thresh,
            evidence_uncertain=bool(state.get("missing_evidence")),
            rag_policy_context=state.get("rag_policy_context")
        )

        self.audit_service.log_event(
            trace_id=state["trace_id"],
            investigation_id=state["investigation_id"],
            payment_id=state["payment_id"],
            actor="DeterministicPolicyEngine",
            event_type="POLICY_VALIDATED",
            metadata={
                "outcome": decision.final_outcome,
                "rule": decision.rule_matched,
                "policy_id": decision.policy_id})

        if decision.final_outcome in ["STOP", "HUMAN_REVIEW", "ESCALATE"]:
            return {"final_decision": decision.final_outcome}

        return {"final_decision": "EXECUTE"}

    def execute_or_review(self, state: InvestigationState) -> Dict[str, Any]:
        """Update executed timestamp."""
        ts = state.get("timestamps", {})
        ts["executed"] = time.time()

        return {"timestamps": ts}

    def record_outcome(self, state: InvestigationState) -> Dict[str, Any]:
        """Record the final decision via tool."""
        try:
            record_res = agent_tools.record_recovery_action(
                state["payment_id"],
                state.get("recommendation", "STOP"),
                state.get("final_decision", "STOP")
            )

            # Idempotency check: don't log if terminal outcome already logged
            logs = self.audit_service.get_investigation_history(state["investigation_id"])
            existing_terminals = [
                log.event_type for log in logs 
                if log.event_type in ["PAYMENT_RECOVERED", "PAYMENT_NOT_RECOVERED", "HUMAN_REVIEW_REQUESTED"]
            ]

            if not existing_terminals:
                final = state.get("final_decision")
                evt_type = None
                if final == "EXECUTE":
                    if record_res.get("success"):
                        evt_type = "PAYMENT_RECOVERED"
                    else:
                        evt_type = "PAYMENT_NOT_RECOVERED"
                elif final in ["STOP", "ESCALATE"]:
                    evt_type = "PAYMENT_NOT_RECOVERED"
                elif final in ["REVIEW", "HUMAN_REVIEW"]:
                    evt_type = "HUMAN_REVIEW_REQUESTED"
                else:
                    evt_type = "PAYMENT_NOT_RECOVERED"
    
                if evt_type:
                    self.audit_service.log_event(
                        trace_id=state["trace_id"],
                        investigation_id=state["investigation_id"],
                        payment_id=state["payment_id"],
                        actor="ReviveAgent",
                        event_type=evt_type,
                        metadata={"final_decision": final, "amount_recovered": record_res.get("amount_recovered", 0.0)}
                    )

            return {"tool_calls": state.get(
                "tool_calls", 0) + 1, "timestamps": {**state.get("timestamps", {}), "end": time.time()}}
        except Exception as e:
            self.audit_service.log_event(
                trace_id=state.get("trace_id", "unknown"),
                investigation_id=state.get("investigation_id", "unknown"),
                payment_id=state.get("payment_id", "unknown"),
                actor="ReviveAgent",
                event_type="TOOL_FAILED",
                metadata={"error": str(e)}
            )
            return {"errors": state.get("errors", []) + [str(e)]}

    def run(self, payment_id: str) -> InvestigationState:
        initial_state: InvestigationState = {
            "trace_id": str(uuid.uuid4()),
            "investigation_id": f"inv_{payment_id}",
            "payment_id": payment_id,
            "recovery_score": 0.0,
            "failure_context": {},
            "customer_context": {},
            "policy_context": {},
            "rag_policy_context": None,
            "counterfactual_outcomes": {},
            "candidate_actions": [],
            "supporting_evidence": [],
            "missing_evidence": [],
            "recommendation": "",
            "confidence": 0.0,
            "final_decision": "",
            "tool_calls": 0,
            "errors": [],
            "timestamps": {}
        }

        return self.graph.invoke(initial_state)
