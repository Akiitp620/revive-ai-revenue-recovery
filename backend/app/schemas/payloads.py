from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime


class DashboardOverview(BaseModel):
    total_recovered: float
    recovery_rate: float
    pending_investigations: int
    
    baselineComparison: Optional[Dict[str, Any]] = None
    efficiency: Optional[List[Dict[str, Any]]] = None
    insight: Optional[Dict[str, Any]] = None
    guardrails: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(extra="allow")


class PaymentBase(BaseModel):
    id: int
    customer_id: int
    amount: float
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)





class PaymentAttemptBase(BaseModel):
    id: int
    status: str
    error_code: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FailureEventBase(BaseModel):
    id: int
    failure_reason: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaymentDetailResponse(PaymentBase):
    attempts: List[PaymentAttemptBase] = []
    failure_events: List[FailureEventBase] = []


class PaymentListResponse(BaseModel):
    items: List[PaymentDetailResponse]
    total: int


class InvestigationCreateRequest(BaseModel):
    payment_id: str


class InvestigationResponse(BaseModel):
    investigation_id: str
    payment_id: str
    payment_amount: float = 0.0
    recommendation: str
    confidence: float
    final_decision: str
    timestamps: Dict[str, float]
    actions: List[Dict[str, Any]] = []


class RecoveryOptionListResponse(BaseModel):
    payment_id: str
    allowed_actions: List[str]


class RecoveryExecuteRequest(BaseModel):
    payment_id: str
    action: str


class OverrideRequest(BaseModel):
    decision: str


class EvaluationSummary(BaseModel):
    dataset_name: str
    sample_count: int
    baseline_recovered_revenue: float
    revive_recovered_revenue: float
    incremental_recovered_revenue: float
    improvement_percentage: float
    recovery_rate: float
    action_selection_accuracy: float
    root_cause_accuracy: float
    unnecessary_intervention_rate: float
    escalation_rate: float
    stop_rule_compliance: float
    policy_violations: float
    average_decision_latency: float
    tool_success_rate: float
    
    model_config = ConfigDict(extra="allow")


class AuditEvent(BaseModel):
    trace_id: str
    investigation_id: str
    payment_id: str
    actor: str
    event_type: str
    metadata_snapshot: Optional[Dict[str, Any]]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditTrailResponse(BaseModel):
    investigation_id: str
    events: List[AuditEvent]
