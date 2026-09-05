from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import Payment, Customer, PaymentAttempt, FailureEvent, RecoveryAction
from app.core.policy import DeterministicPolicyEngine

def _get_db_id(payment_id: str) -> int:
    try:
        return int(payment_id.replace("pay_", ""))
    except ValueError:
        return 0

def get_payment(payment_id: str, db_session: Optional[Session] = None) -> Dict[str, Any]:
    """Implementation to load a payment context from DB."""
    db_id = _get_db_id(payment_id)
    db = db_session if db_session else SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == db_id).first()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found in database.")
        return {
            "payment_id": payment_id,
            "amount": float(payment.amount),
            "status": payment.status,
            "currency": payment.currency
        }
    finally:
        if db_session is None:
            db.close()

def get_customer_history(payment_id: str) -> Dict[str, Any]:
    """Load customer history from DB based on the payment's customer."""
    db_id = _get_db_id(payment_id)
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == db_id).first()
        if not payment or not payment.customer:
            return {"unavailable": True, "reason": "Customer not found"}
        
        customer = payment.customer
        
        # Calculate lifetime value and success rate
        total_value = 0.0
        success_count = 0
        total_count = len(customer.payments)
        
        for p in customer.payments:
            if p.status in ["success", "recovered"]:
                success_count += 1
                total_value += float(p.amount)
                
        success_rate = success_count / total_count if total_count > 0 else 0.0
        
        return {
            "customer_id": customer.external_id,
            "success_rate": round(success_rate, 2),
            "lifetime_value": round(total_value, 2)
        }
    finally:
        db.close()

def get_payment_attempts(payment_id: str) -> List[Dict[str, Any]]:
    """Load previous attempts from the database."""
    db_id = _get_db_id(payment_id)
    db = SessionLocal()
    try:
        attempts = db.query(PaymentAttempt).filter(PaymentAttempt.payment_id == db_id).all()
        return [
            {
                "attempt_time": att.attempt_time.isoformat() if att.attempt_time else None,
                "status": att.status,
                "error_code": att.error_code
            }
            for att in attempts
        ]
    finally:
        db.close()

def get_failure_context(payment_id: str) -> Dict[str, Any]:
    """Load the failure context from the database."""
    db_id = _get_db_id(payment_id)
    db = SessionLocal()
    try:
        event = db.query(FailureEvent).filter(FailureEvent.payment_id == db_id).first()
        if not event:
            return {"unavailable": True, "reason": "Failure context not found"}
        
        return {
            "error_code": event.failure_reason,
            "context": event.context_snapshot
        }
    finally:
        db.close()

def get_merchant_policy(merchant_id: str) -> Dict[str, Any]:
    """Retrieve merchant policy using DeterministicPolicyEngine canonical rules."""
    engine = DeterministicPolicyEngine()
    
    # We provide the fields the dashboard expects (allowlist, version)
    # as well as the newly requested fields from the prompt.
    return {
        "version": engine.policy_version,
        "allowlist": ["RETRY_LATER", "REMINDER", "RETRY_NOW", "ALTERNATE_PAYMENT", "HUMAN_REVIEW", "STOP"],
        "retry_limit": engine.MAX_RETRIES,
        "auto_execution_threshold": engine.MAX_AUTO_ACTION_VALUE,
        "human_approval_threshold": engine.HIGH_VALUE_THRESHOLD,
        "stop_rules": list(engine.HARD_DECLINE_ERRORS),
        "min_recovery_threshold": 5.0
    }

def simulate_recovery_action(action: str, payment_id: str) -> Dict[str, Any]:
    """Simulate recovery action metrics deterministically for the UI."""
    payment = get_payment(payment_id)
    amount = payment.get("amount")
    
    if amount is None:
        raise ValueError(f"Payment {payment_id} missing amount.")
        
    db_id = _get_db_id(payment_id)
    db = SessionLocal()
    try:
        from app.models import RecoveryPrediction
        prediction = db.query(RecoveryPrediction).join(FailureEvent).filter(FailureEvent.payment_id == db_id).first()
        from app.core.simulator import ActionSimulator
        sim = ActionSimulator()
        sim_result = sim.simulate_operational_outcome(action, amount, prediction)
    finally:
        db.close()
        
    policy = get_merchant_policy("merchant")
    is_allowed = action in policy.get("allowlist", [])
    sim_result["policy_status"] = "allowed" if is_allowed else "blocked"
    
    return sim_result

def record_recovery_action(payment_id: str, action: str, outcome: str, db_session: Optional[Session] = None) -> Dict[str, Any]:
    """Record the action and its deterministic outcome in the database."""
    db_id = _get_db_id(payment_id)
    db = db_session if db_session else SessionLocal()
    try:
        failure_event = db.query(FailureEvent).filter(FailureEvent.payment_id == db_id).first()
        if not failure_event:
            raise ValueError(f"Cannot record action: FailureEvent not found for payment {payment_id}")
            
        from app.models import RecoveryOutcome, RecoveryAction
        
        # Idempotency check: if already executed this terminal action, return it
        existing_action = db.query(RecoveryAction).filter(
            RecoveryAction.failure_event_id == failure_event.id,
            RecoveryAction.action_type == action,
            RecoveryAction.status == outcome
        ).first()
        
        if existing_action:
            result = {
                "status": "already_recorded",
                "action_id": existing_action.id,
                "action": action,
                "outcome": outcome
            }
            if existing_action.outcome:
                result["success"] = existing_action.outcome.success
                result["amount_recovered"] = existing_action.outcome.amount_recovered
            return result

        recovery_action = RecoveryAction(
            failure_event_id=failure_event.id,
            action_type=action,
            status=outcome
        )
        db.add(recovery_action)
        db.flush()
        
        result = {
            "status": "recorded",
            "action_id": recovery_action.id,
            "action": action,
            "outcome": outcome
        }
        
        if outcome == "EXECUTE":
            # Simulate real outcome
            from app.models import RecoveryPrediction
            from app.core.simulator import ActionSimulator
            
            prediction = db.query(RecoveryPrediction).filter(RecoveryPrediction.failure_event_id == failure_event.id).first()
            payment = get_payment(payment_id, db_session=db)
            amount = payment.get("amount", 0.0)
            
            sim = ActionSimulator()
            sim_result = sim.simulate_operational_outcome(action, amount, prediction)
            
            if sim_result.get("unavailable"):
                raise ValueError("Prediction unavailable, cannot execute recovery.")
                
            recovery_outcome = RecoveryOutcome(
                recovery_action_id=recovery_action.id,
                success=sim_result["success"],
                amount_recovered=sim_result["amount_recovered"]
            )
            db.add(recovery_outcome)
            result["success"] = sim_result["success"]
            result["amount_recovered"] = sim_result["amount_recovered"]

        db.commit()
        return result
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error persisting RecoveryAction: {e}")
    finally:
        if db_session is None:
            db.close()
