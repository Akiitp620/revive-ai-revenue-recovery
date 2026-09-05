from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import asyncio

from app.database import get_db
from app.schemas.payloads import (
    DashboardOverview,
    PaymentListResponse,
    PaymentDetailResponse,
    InvestigationCreateRequest,
    InvestigationResponse,
    RecoveryOptionListResponse,
    RecoveryExecuteRequest,
    OverrideRequest,
    EvaluationSummary,
    AuditTrailResponse,
    AuditEvent
)
from app.core import api_service

router = APIRouter()


@router.get("/dashboard/overview", response_model=DashboardOverview)
def get_dashboard(db: Session = Depends(get_db)):
    data = api_service.get_dashboard_metrics(db)
    return DashboardOverview(**data)


@router.get("/payments", response_model=PaymentListResponse)
def get_payments(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)):
    data = api_service.get_payments(db, skip=skip, limit=limit)
    return PaymentListResponse(**data)


@router.get("/payments/{payment_id}", response_model=PaymentDetailResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = api_service.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentDetailResponse.model_validate(payment)


@router.post("/investigations", response_model=InvestigationResponse)
def create_investigation(
        request: InvestigationCreateRequest,
        db: Session = Depends(get_db)):
    state = api_service.execute_investigation(db, request.payment_id)
    return InvestigationResponse(
        investigation_id=state["investigation_id"],
        payment_id=state["payment_id"],
        recommendation=state.get("recommendation", "UNKNOWN"),
        confidence=state.get("confidence", 0.0),
        final_decision=state.get("final_decision", "UNKNOWN"),
        timestamps=state.get("timestamps", {})
    )


@router.get("/investigations/{investigation_id}",
            response_model=InvestigationResponse)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    state = api_service.get_investigation_state(db, investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return InvestigationResponse(**state)


@router.get("/investigations/{investigation_id}/stream")
async def stream_investigation(
        investigation_id: str,
        db: Session = Depends(get_db)):
    """SSE stream for real investigation progress."""
    import json

    initial_events = api_service.get_audit_history(db, investigation_id)
    if not initial_events:
        raise HTTPException(status_code=404, detail="Investigation not found")

    async def event_generator():
        last_event_id = 0
        terminal_events = {
            "HUMAN_REVIEW_REQUESTED",
            "PAYMENT_RECOVERED",
            "PAYMENT_NOT_RECOVERED",
            "FALLBACK_APPLIED",
            "TOOL_FAILED"
        }

        while True:
            # Expire session to fetch latest changes from DB if it's running
            # concurrently
            db.expire_all()
            events = api_service.get_audit_history(db, investigation_id)

            new_events = [
                e for e in events if getattr(
                    e, 'id', 0) > last_event_id]

            for evt in new_events:
                data = {
                    "event_type": evt.event_type,
                    "metadata": evt.metadata_snapshot,
                    "timestamp": evt.timestamp.isoformat()
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_event_id = getattr(evt, 'id', last_event_id)

                if evt.event_type in terminal_events:
                    return

            # Since our prototype executes synchronously, it will find all events on the first iteration and return.
            # If an async worker was added later, this sleep would prevent
            # tight polling.
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/recovery/options/{payment_id}",
            response_model=RecoveryOptionListResponse)
def get_recovery_options(payment_id: str, db: Session = Depends(get_db)):
    data = api_service.get_recovery_options(db, payment_id)
    return RecoveryOptionListResponse(**data)


@router.post("/recovery/execute")
def execute_recovery(
        request: RecoveryExecuteRequest,
        db: Session = Depends(get_db)):
    try:
        success = api_service.execute_recovery_action(
            db, request.payment_id, request.action)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to execute action")
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post("/decisions/{investigation_id}/override")
def override_decision(
        investigation_id: str,
        request: OverrideRequest,
        db: Session = Depends(get_db)):
    success = api_service.override_decision(
        db, investigation_id, request.decision)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to override decision")
    return {"status": "success"}


@router.get("/evaluations/latest", response_model=EvaluationSummary)
def get_evaluations(db: Session = Depends(get_db)):
    data = api_service.get_latest_evaluations(db)
    return EvaluationSummary(**data)


@router.get("/audit/{investigation_id}", response_model=AuditTrailResponse)
def get_audit_history(investigation_id: str, db: Session = Depends(get_db)):
    history = api_service.get_audit_history(db, investigation_id)
    events = [AuditEvent.model_validate(h) for h in history]
    return AuditTrailResponse(investigation_id=investigation_id, events=events)
