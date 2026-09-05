import os
import sys
import pandas as pd
from datetime import timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models import (
    Merchant, Customer, Payment, PaymentAttempt, 
    FailureEvent, RecoveryAction, RecoveryOutcome
)

def seed_db(csv_path: str = None, limit: int = 500):
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "output", "development.csv")
        
    if not os.path.exists(csv_path):
        print(f"Dataset {csv_path} not found. Please run generator.py first.")
        return

    print(f"Reading synthetic dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if limit:
        df = df.head(limit)
        
    db = SessionLocal()
    
    from app.ml.inference import RecoveryModel
    from app.models import RecoveryPrediction
    try:
        model = RecoveryModel()
    except Exception as e:
        print(f"Warning: Could not load RecoveryModel: {e}")
        model = None
    
    records_inserted = {
        "Merchant": 0,
        "Customer": 0,
        "Payment": 0,
        "PaymentAttempt": 0,
        "FailureEvent": 0,
        "RecoveryAction": 0,
        "RecoveryOutcome": 0,
        "RecoveryPrediction": 0
    }
    
    print(f"Seeding {len(df)} records into operational tables...")
    
    try:
        for idx, row in df.iterrows():
            created_at = pd.to_datetime(row["timestamp"]).replace(tzinfo=timezone.utc)
            
            # Idempotency check for Payment
            existing_payment = db.query(Payment).filter(
                Payment.amount == float(row["amount"]),
                Payment.currency == row["currency"],
                Payment.created_at == created_at
            ).first()
            
            if existing_payment:
                continue
                
            # Merchant
            merchant = db.query(Merchant).filter(Merchant.name == row["merchant_id"]).first()
            if not merchant:
                merchant = Merchant(name=row["merchant_id"])
                db.add(merchant)
                db.flush()
                records_inserted["Merchant"] += 1
                
            # Customer
            customer = db.query(Customer).filter(Customer.external_id == row["customer_id"]).first()
            if not customer:
                customer = Customer(merchant_id=merchant.id, external_id=row["customer_id"])
                db.add(customer)
                db.flush()
                records_inserted["Customer"] += 1
                
            # Payment
            payment_status = "recovered" if row["eventual_outcome"] else "failed"
            payment = Payment(
                customer_id=customer.id,
                amount=float(row["amount"]),
                currency=row["currency"],
                status=payment_status,
                created_at=created_at
            )
            db.add(payment)
            db.flush()
            records_inserted["Payment"] += 1
            
            # Failure Event
            failure_event = FailureEvent(
                payment_id=payment.id,
                failure_reason=row["error_code"],
                created_at=created_at
            )
            db.add(failure_event)
            db.flush()
            records_inserted["FailureEvent"] += 1
            
            # Recovery Prediction
            if model:
                error_code = row["error_code"]
                if pd.isna(error_code):
                    error_code = None
                    
                event_dict = {
                    "amount": float(row["amount"]),
                    "past_attempts": int(row.get("past_attempts", 0)),
                    "error_code": error_code,
                    "payment_method": row.get("payment_method", "card")
                }
                prob = model.predict_probability(event_dict)
                prediction = RecoveryPrediction(
                    failure_event_id=failure_event.id,
                    model_version=model.model_version,
                    feature_snapshot=event_dict,
                    recovery_probability=prob,
                    created_at=created_at
                )
                db.add(prediction)
                db.flush()
                records_inserted["RecoveryPrediction"] += 1
            
            # Payment Attempts (history prior to failure)
            past_attempts = int(row.get("past_attempts", 0))
            for _ in range(past_attempts):
                attempt = PaymentAttempt(
                    payment_id=payment.id,
                    status="failed",
                    error_code=row["error_code"],
                    created_at=created_at
                )
                db.add(attempt)
                records_inserted["PaymentAttempt"] += 1
                
            # Recovery Action & Outcome (if simulated/acted upon)
            action_type = row.get("best_action", "STOP")
            is_recovered = bool(row.get("eventual_outcome", False))
            amount_recovered = float(row.get("amount_recovered", 0.0))
            
            # We seed a RecoveryAction
            recovery_action = RecoveryAction(
                failure_event_id=failure_event.id,
                action_type=action_type,
                status="completed" if is_recovered else "pending",
                created_at=created_at
            )
            db.add(recovery_action)
            db.flush()
            records_inserted["RecoveryAction"] += 1
            
            # We seed a RecoveryOutcome if an action was actually executed
            if action_type != "STOP" or is_recovered:
                outcome = RecoveryOutcome(
                    recovery_action_id=recovery_action.id,
                    success=is_recovered,
                    amount_recovered=amount_recovered,
                    created_at=created_at
                )
                db.add(outcome)
                records_inserted["RecoveryOutcome"] += 1
                
        db.commit()
        
        print("\nSeeding Complete! Records inserted:")
        for table, count in records_inserted.items():
            print(f"  {table}: {count}")
            
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
