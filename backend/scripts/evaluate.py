from langchain_community.chat_models import FakeListChatModel
from app.database import SessionLocal, engine
from app.models import EvaluationRun, EvaluationRunMetric, Base
from app.core.evaluation import compute_all_metrics
from app.core.policy import DeterministicPolicyEngine
from app.core.agent import ReviveAgent, AgentRecommendation
from app.core.baseline import BaselinePolicy
from app.ml.inference import RecoveryModel
from app.core.simulator import ActionSimulator
import os
import sys
import json
import time
import pandas as pd
from typing import Dict, Any

# Ensure backend path is configured
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# A smarter Fake LLM for the agent so it doesn't just output 'RETRY_LATER'
# everywhere

class EvaluationFakeLLM(FakeListChatModel):
    def with_structured_output(self, schema):
        class StructLLM:
            def invoke(self, prompt):
                # Basic simulated logic based on text in prompt
                strategy = "RETRY_LATER"
                confidence = 0.85
                root_cause = "unknown"
                if "insufficient_funds" in prompt:
                    strategy = "RETRY_LATER"
                    root_cause = "insufficient_funds"
                elif "stolen_card" in prompt or "lost_card" in prompt or "fraud" in prompt:
                    strategy = "STOP"
                    root_cause = "fraud"
                elif "timeout" in prompt:
                    strategy = "RETRY_NOW"
                    root_cause = "gateway_timeout"

                return AgentRecommendation(
                    strategy=strategy,
                    confidence=confidence,
                    supporting_evidence=["mocked_evidence"],
                    missing_evidence=[],
                    root_cause=root_cause
                )
        return StructLLM()


def map_dataset_action_to_agent_action(action: str) -> str:
    """Map the dataset's ground truth 'best_action' to the Agent's vocabulary."""
    mapping = {
        "manual_review": "HUMAN_REVIEW",
        "stop_and_notify": "STOP",
        "stop": "STOP",
        "wait_and_retry": "RETRY_LATER",
        "wait_for_paycheck": "RETRY_LATER",
        "immediate_retry": "RETRY_NOW"
    }
    return mapping.get(action, "STOP")


def run_evaluation(use_real_llm: bool = False):
    print("Loading held_out.csv...")
    df = pd.read_csv("data/output/held_out.csv")

    if len(df) != 1500:
        raise ValueError(f"Evaluation must strictly use the 1500 held-out cases. Found {len(df)}.")

    baseline_policy = BaselinePolicy()
    action_simulator = ActionSimulator()
    
    try:
        recovery_model = RecoveryModel(model_version="v1.0")
    except FileNotFoundError:
        print("WARNING: RecoveryModel not found. Falling back to simple heuristic.")
        recovery_model = None

    # Initialize Policy Engine
    policy_engine = DeterministicPolicyEngine()
    merchant_allowlist = ["RETRY_NOW", "RETRY_LATER", "ALTERNATE_PAYMENT", "REMINDER"]
    min_recovery_threshold = 0.5

    revive_outcomes = []
    baseline_outcomes = []

    print(f"Evaluating {len(df)} cases...")

    for idx, row in df.iterrows():
        event_dict = {
            "payment_id": str(row["payment_id"]),
            "amount": float(row["amount"]),
            "error_code": str(row["error_code"]),
            "past_attempts": int(row["past_attempts"]),
            "payment_method": str(row.get("payment_method", "card")),
            "recoverable": bool(row["recoverable"]),
            "best_action": str(row["best_action"]),
            "amount_recovered": float(row["amount_recovered"])
        }

        # 1. Baseline Evaluation
        b_action = baseline_policy.evaluate(event_dict)
        b_rec, b_rev = baseline_policy.simulate_outcome(b_action, event_dict)
        baseline_outcomes.append({
            "action": b_action,
            "best_action": event_dict["best_action"],
            "amount_recovered": b_rev if b_rec else 0.0,
            "recoverable": event_dict["recoverable"]
        })

        # 2. REVIVE Deterministic Evaluation (No LLM)
        base_probability = 0.5
        if recovery_model:
            base_probability = recovery_model.predict_probability(event_dict)

        counterfactuals = {}
        best_permitted_action = "STOP"
        best_permitted_action_outcome = -float('inf')
        best_action_final_decision = "STOP"

        for action in action_simulator.ACTIONS:
            cost = action_simulator.COSTS.get(action, 0.0)
            
            if action == "STOP":
                prob = 0.0
            else:
                prob = base_probability
                if action == "RETRY_NOW":
                    prob *= 0.5
                elif action == "HUMAN_REVIEW":
                    prob = min(0.95, prob * 1.5)
            
            expected_recovery = event_dict["amount"] * prob
            enr = expected_recovery - cost
            
            counterfactuals[action] = {
                "probability": prob,
                "expected_recovery": expected_recovery,
                "intervention_cost": cost,
                "expected_net_recovery": enr
            }

            if action == "STOP":
                if enr > best_permitted_action_outcome:
                    best_permitted_action_outcome = enr
                    best_permitted_action = "STOP"
                    best_action_final_decision = "STOP"
                continue

            pol_dec = policy_engine.evaluate(
                proposed_action=action,
                event=event_dict,
                expected_net_recovery=enr,
                merchant_allowlist=merchant_allowlist,
                min_recovery_threshold=min_recovery_threshold,
                evidence_uncertain=False
            )

            if pol_dec.final_outcome == "STOP":
                continue

            if enr > best_permitted_action_outcome:
                best_permitted_action_outcome = enr
                best_permitted_action = action
                best_action_final_decision = pol_dec.final_outcome
        
        agent_action = best_permitted_action
        agent_final = best_action_final_decision
        
        if agent_final == "AUTHORIZED":
            agent_final = "EXECUTE"

        mapped_best = map_dataset_action_to_agent_action(event_dict["best_action"])
        selection_gap = best_permitted_action_outcome - counterfactuals[agent_action]["expected_net_recovery"]

        # 3. Simulate Actual Outcome using Ground Truth
        a_rec = False
        a_rev = 0.0
        
        actual_action_taken = agent_action
        if agent_final in ["HUMAN_REVIEW", "ESCALATE", "REVIEW"]:
            actual_action_taken = "HUMAN_REVIEW"

        if actual_action_taken != "STOP":
            actual_outcome = action_simulator.evaluate_action(actual_action_taken, event_dict["amount"], event_dict)
            if actual_outcome.get("expected_recovery", 0) > 0 and event_dict["recoverable"]:
                a_rec = True
                a_rev = event_dict["amount_recovered"]

        revive_outcomes.append({
            "action": agent_action,
            "best_action": mapped_best,
            "best_permitted_action": best_permitted_action,
            "selection_gap": selection_gap,
            "counterfactual_outcomes": counterfactuals,
            "amount_recovered": a_rev,
            "recoverable": event_dict["recoverable"],
            "diagnosed_root_cause": "unknown", # No LLM to diagnose
            "ground_truth_error_code": event_dict["error_code"],
            "final_decision": agent_final,
            "is_hard_decline": event_dict["error_code"] in BaselinePolicy.HARD_DECLINE_ERRORS,
            "allowlist": merchant_allowlist,
            "latency": 0.001,
            "tool_calls": 0,
            "tool_errors": 0
        })

    metrics = compute_all_metrics(revive_outcomes, baseline_outcomes, dataset_name="held_out")

    # Expose average selection gap in summary metrics
    total_gap = sum([r.get("selection_gap", 0.0)
                    for r in revive_outcomes if r.get("selection_gap") is not None])
    metrics["average_selection_gap"] = total_gap / max(1, len(revive_outcomes))

    print("\n--- Evaluation Complete ---")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")

    # Save summary metrics to JSON
    out_file = "data/output/evaluation_results.json"
    with open(out_file, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved metrics to {out_file}")

    # Save detailed outcomes with counterfactuals
    details_file = "data/output/evaluation_details.json"
    with open(details_file, "w") as f:
        json.dump({
            "note": "These are simulator-based prototype results. Do not describe them as causal real-world effects.",
            "cases": revive_outcomes
        }, f, indent=2)
    print(f"Saved detailed counterfactual outcomes to {details_file}")

    # Save to PostgreSQL
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

        run_record = EvaluationRun(
            model_version="fake_llm_1.0",
            policy_version="v1",
            dataset_version="held_out_1.0"
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)

        for k, v in metrics.items():
            if isinstance(v, (float, int)):
                metric_record = EvaluationRunMetric(
                    evaluation_run_id=run_record.id,
                    metric_name=k,
                    metric_value=float(v)
                )
                db.add(metric_record)
        db.commit()
        print("Persisted summary results to PostgreSQL.")
    except Exception as e:
        print(f"Error persisting to PostgreSQL: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    run_evaluation()
