from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models import AuditLog


class InvestigationAuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        trace_id: str,
        investigation_id: str,
        payment_id: str,
        actor: str,
        event_type: str,
        metadata: Dict[str, Any]
    ) -> AuditLog:
        """
        Append-only function to log an investigation event.
        Chain-of-thought is strictly omitted.
        """
        # We can implement a naive check here for chain-of-thought
        # by restricting the size of the metadata JSON or explicitly stripping
        # known CoT keys.
        safe_metadata = {
            k: v for k, v in metadata.items()
            if "thought" not in k.lower() and "reasoning" not in k.lower()
        }

        audit_entry = AuditLog(
            trace_id=trace_id,
            investigation_id=investigation_id,
            payment_id=payment_id,
            actor=actor,
            event_type=event_type,
            metadata_snapshot=safe_metadata
        )

        self.db.add(audit_entry)
        self.db.commit()
        self.db.refresh(audit_entry)
        return audit_entry

    def get_investigation_history(
            self, investigation_id: str) -> List[AuditLog]:
        """
        Retrieves the audit history for a specific investigation, ordered chronologically.
        """
        return self.db.query(AuditLog).filter(
            AuditLog.investigation_id == investigation_id
        ).order_by(AuditLog.timestamp.asc()).all()
