'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  Send,
} from 'lucide-react';

import { getInvestigation, getAuditTimeline } from '@/lib/api/recovery';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { SectionHeader } from '@/components/shared/section-header';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { EvidenceList } from '@/components/investigation/evidence-list';
import { CustomerContext } from '@/components/investigation/customer-context';
import { RecoveryActionCard } from '@/components/investigation/recovery-action-card';
import { AuditTimeline } from '@/components/investigation/audit-timeline';
import { RecoveryTrace } from '@/components/investigation/recovery-trace';
import { PolicyCard } from '@/components/investigation/policy-card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { formatCurrency, formatPercentage } from '@/lib/utils/formatting';

export default function PaymentInvestigationPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;

  const [payment, setPayment] = useState(null);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigation, setInvestigation] = useState(null);
  const [error, setError] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null);
  const [approvalState, setApprovalState] = useState('pending');
  const [approvalSubmitting, setApprovalSubmitting] = useState(false);
  const [approvalError, setApprovalError] = useState(null);
  const [showPolicyModal, setShowPolicyModal] = useState(false);

  const EVENT_MAPPING = {
    'ACTION_SELECTED': 'Action selected',
    'HUMAN_REVIEW_REQUESTED': 'Human approval requested',
    'PAYMENT_RECOVERED': 'Payment recovered',
    'PAYMENT_NOT_RECOVERED': 'Payment not recovered',
    'FALLBACK_APPLIED': 'Fallback applied',
    'TOOL_FAILED': 'Tool failed',
    'PAYMENT_LOADED': 'Payment loaded',
    'FAILURE_DIAGNOSED': 'Failure diagnosed',
    'CONTEXT_EVALUATED': 'Customer context evaluated',
    'PROBABILITY_CALCULATED': 'Recovery probability calculated',
    'OPTIONS_EVALUATED': 'Recovery options evaluated',
    'POLICY_EVALUATED': 'Merchant policy evaluated'
  };

  useEffect(() => {
    import('@/lib/mock/payments').then(({ findPayment }) => {
      setPayment(findPayment(id));
    });
  }, [id]);

  useEffect(() => {
    if (!isInvestigating) return;

    let active = true;
    let eventSource = null;

    getInvestigation(id)
      .then(async (data) => {
        if (!active) return;

        let initialTimeline = data.timeline || [];
        if (data.investigation_id) {
            try {
               const auditEvents = await getAuditTimeline(id);
               if (auditEvents && auditEvents.length > 0) {
                   initialTimeline = auditEvents.map(e => ({
                       time: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
                       event: EVENT_MAPPING[e.event_type] || e.event_type,
                       status: 'done'
                   }));

                   const hasRequested = auditEvents.some(e => e.event_type === 'HUMAN_REVIEW_REQUESTED');
                   const hasOutcome = auditEvents.some(e => e.event_type === 'PAYMENT_RECOVERED' || e.event_type === 'PAYMENT_NOT_RECOVERED');

                   if (hasOutcome) {
                       setApprovalState('completed');
                   } else if (hasRequested) {
                       setApprovalState('requested');
                   }
               }
            } catch (e) {
               console.error("Failed to load timeline", e);
            }
        }

        setInvestigation({ ...data, timeline: initialTimeline });
        const recommended = data.actions.find((a) => a.recommended) || data.actions[0];
        setSelectedAction(recommended);

        if (data.investigation_id) {
          eventSource = new EventSource(`/api/v1/investigations/${data.investigation_id}/stream`);
          eventSource.onmessage = (e) => {
            if (!active) return;
            const newEvent = JSON.parse(e.data);

            if (newEvent.event_type === 'HUMAN_REVIEW_REQUESTED') {
                setApprovalState(prev => prev === 'completed' ? 'completed' : 'requested');
            } else if (newEvent.event_type === 'PAYMENT_RECOVERED' || newEvent.event_type === 'PAYMENT_NOT_RECOVERED') {
                setApprovalState('completed');
            }
            setInvestigation(prev => {
              if (!prev) return prev;
              const formattedTime = new Date(newEvent.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

              // Only add if not duplicate (optional, but React state updates could be tricky)
              const eventStr = EVENT_MAPPING[newEvent.event_type] || newEvent.event_type;
              return {
                ...prev,
                timeline: [
                  ...prev.timeline,
                  { time: formattedTime, event: eventStr, status: 'done' }
                ]
              };
            });
          };
          eventSource.onerror = () => {
            if (eventSource) eventSource.close();
          };
        }
      })
      .catch(() => { if (active) setError(true); });

    return () => {
      active = false;
      if (eventSource) eventSource.close();
    };
  }, [id, isInvestigating]);

  function retry() {
    setError(false);
    setInvestigation(null);
    getInvestigation(id)
      .then((data) => {
        setInvestigation({ ...data, timeline: [] });
        const recommended = data.actions.find((a) => a.recommended) || data.actions[0];
        setSelectedAction(recommended);
      })
      .catch(() => setError(true));
  }

  async function handleExecute() {
    if (!selectedAction || !investigation?.investigation_id || approvalState !== 'pending' || approvalSubmitting) return;
    setApprovalSubmitting(true);
    setApprovalError(null);

    try {
      const { executeRecovery, getAuditTimeline } = await import('@/lib/api/recovery');
      const result = await executeRecovery(id, selectedAction.id);

      if (!result || result.error) {
        setApprovalError(result?.detail || result?.error || 'Approval request failed. The backend did not confirm the request.');
        return;
      }

      // Confirmed backend success — transition state
      setApprovalState('requested');

      // Re-fetch timeline to show the persisted HUMAN_REVIEW_REQUESTED event
      try {
        const freshEvents = await getAuditTimeline(id);
        if (freshEvents && freshEvents.length > 0) {
          const mapped = freshEvents.map(e => ({
            time: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
            event: EVENT_MAPPING[e.event_type] || e.event_type,
            status: 'done'
          }));
          setInvestigation(prev => prev ? { ...prev, timeline: mapped } : prev);

          const hasRequested = freshEvents.some(e => e.event_type === 'HUMAN_REVIEW_REQUESTED');
          const hasOutcome = freshEvents.some(e => e.event_type === 'PAYMENT_RECOVERED' || e.event_type === 'PAYMENT_NOT_RECOVERED');
          if (hasOutcome) setApprovalState('completed');
          else if (hasRequested) setApprovalState('requested');
        }
      } catch (timelineErr) {
        // Non-fatal: approval succeeded, timeline refresh failed
        console.error('Timeline refresh failed', timelineErr);
      }
    } catch (err) {
      setApprovalError(err?.message || 'Unexpected error. Please try again.');
    } finally {
      setApprovalSubmitting(false);
    }
  }

  if (error) {
    return (
      <AppShell>
        <PageContainer>
          <div className="rounded-xl border border-border bg-card">
            <ErrorState title="Unable to load investigation data" onRetry={retry} />
          </div>
        </PageContainer>
      </AppShell>
    );
  }

  if (!payment) {
    return (
      <AppShell>
        <PageContainer>
          <LoadingSkeleton variant="cards" />
        </PageContainer>
      </AppShell>
    );
  }

  const diagnosis = investigation?.diagnosis;
  const customer = investigation?.customer;
  const recovery = investigation?.recovery;
  const recommendation = investigation?.recommendation;
  const actions = investigation?.actions;
  const policy = investigation?.policy;
  const timeline = investigation?.timeline;
  const recoveryTrace = investigation?.recoveryTrace;
  const amount = payment.amount;

  return (
    <AppShell>
      <PageContainer>
        <button
          onClick={() => router.push('/payments')}
          className="mb-4 flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Payments
        </button>

        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 rounded-xl border border-border bg-card p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-destructive">Failed Payment</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">{payment.transactionId}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{payment.customer} · {payment.paymentMethod}</p>
          </div>
          <div className="flex items-center gap-6">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Amount</p>
              <p className="text-2xl font-bold text-foreground tabular-nums">{formatCurrency(amount)}</p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Recovery Probability</p>
              <p className="text-2xl font-bold text-primary tabular-nums">{formatPercentage(payment.recoveryProbability)}</p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Expected Recovery</p>
              <p className="text-2xl font-bold text-success tabular-nums">{formatCurrency(payment.expectedRecovery)}</p>
            </div>
          </div>
        </div>

        {!isInvestigating && !investigation && (
          <section className="mb-8 flex flex-col items-center justify-center rounded-xl border border-border bg-card py-12 text-center">
            <h3 className="mb-2 text-lg font-semibold text-foreground">Ready to Investigate</h3>
            <p className="mb-6 max-w-md text-sm text-muted-foreground">
              Run the AI decision engine to diagnose this failure and determine the highest-value recovery action.
            </p>
            <Button onClick={() => setIsInvestigating(true)} size="lg" className="gap-2">
              Investigate Payment
            </Button>
          </section>
        )}

        {isInvestigating && !investigation && (
          <section className="mb-8">
            <LoadingSkeleton variant="cards" />
          </section>
        )}

        {investigation && (
          <>
            {/* Failure Diagnosis + Customer Context */}
        <section className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Why did this payment fail?" />
            <p className="mb-4 text-sm font-medium text-primary">{diagnosis.primary}</p>
            <EvidenceList items={diagnosis.evidence} />
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Customer Context" />
            <CustomerContext customer={customer} />
          </div>
        </section>

        {/* Recovery Opportunity */}
        <section className="mb-8 rounded-xl border border-border bg-card p-5">
          <SectionHeader title="Recovery Opportunity" description="Expected value based on recovery probability" />
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
              <span className="text-xs text-muted-foreground">Payment Amount</span>
              <span className="text-sm font-semibold text-foreground tabular-nums">{formatCurrency(amount)}</span>
            </div>
            <span className="text-muted-foreground">×</span>
            <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
              <span className="text-xs text-muted-foreground">Probability</span>
              <span className="text-sm font-semibold text-primary tabular-nums">{formatPercentage(recovery.probability)}</span>
            </div>
            <span className="text-muted-foreground">=</span>
            <div className="flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
              <span className="text-xs text-muted-foreground">Expected Recovery</span>
              <span className="text-base font-bold text-success tabular-nums">{formatCurrency(recovery.expectedAmount)}</span>
            </div>
          </div>
        </section>

        {/* Recovery Action Simulator */}
        <section className="mb-8">
          <SectionHeader title="Compare Recovery Actions" description="Select an action to update the recommendation analysis" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {actions.map((action) => (
              <RecoveryActionCard
                key={action.id}
                action={action}
                selected={selectedAction?.id === action.id}
                onSelect={setSelectedAction}
              />
            ))}
          </div>
        </section>

        {/* Action Comparison + Policy */}
        <section className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Selected Action" description={selectedAction?.label} />
            <div className="mb-4 rounded-lg border border-primary/30 bg-primary/5 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-foreground">{selectedAction?.label}</span>
                <span className="text-sm font-bold text-success tabular-nums">
                  {formatCurrency(selectedAction?.expectedNetRecovery !== undefined ? selectedAction?.expectedNetRecovery : selectedAction?.expectedRecovery)}
                </span>
              </div>
            </div>
            <p className="mb-3 text-xs font-medium text-muted-foreground">Why this action:</p>
            <ul className="space-y-2">
              {recommendation.reasons.map((reason, index) => (
                <li key={index} className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                  <span className="text-xs text-foreground">{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Merchant Recovery Policy" />
            <PolicyCard policy={policy} amount={amount} />
          </div>
        </section>

        {/* Why Not Auto-Execute */}
        {investigation.policy.requiresApproval ? (
          <section className="mb-8 rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Why wasn't this automatically executed?" />
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-success">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Supporting Factors
                </p>
                <ul className="space-y-2">
                  {investigation.supportingFactors.map((factor, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-foreground">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-destructive">
                  <XCircle className="h-3.5 w-3.5" /> Blocking Factors
                </p>
                <ul className="space-y-2">
                  {investigation.blockingFactors.map((factor, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-foreground">
                      <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-lg bg-warning/10 px-4 py-2.5 ring-1 ring-warning/20">
              <Clock className="h-4 w-4 text-warning" />
              <span className="text-sm font-medium text-warning">Awaiting Human Approval</span>
            </div>
          </section>
        ) : (
          <section className="mb-8 rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Execution Status" />
            <div className="mt-4 flex items-center gap-2 rounded-lg bg-success/10 px-4 py-2.5 ring-1 ring-success/20">
              <CheckCircle2 className="h-4 w-4 text-success" />
              <span className="text-sm font-medium text-success">Auto-execution permitted</span>
            </div>
          </section>
        )}

        {/* Action Controls */}
        <section className="mb-8 flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-3">
            {approvalState === 'pending' && investigation.policy.requiresApproval && (
              <Button
                className="gap-2"
                onClick={handleExecute}
                disabled={approvalSubmitting}
              >
                <Send className="h-4 w-4" />
                {approvalSubmitting ? 'Requesting…' : 'Request Approval'}
              </Button>
            )}
            {approvalState === 'pending' && !investigation.policy.requiresApproval && (
              <div className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2.5 text-sm text-muted-foreground">
                <ShieldCheck className="h-4 w-4" />
                Approval not required — this transaction is within auto-execution limits
              </div>
            )}
            {approvalState === 'requested' && (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-lg bg-success/10 px-4 py-2.5 ring-1 ring-success/20">
                  <CheckCircle2 className="h-4 w-4 text-success" />
                  <span className="text-sm font-medium text-success">Approval requested — pending review</span>
                </div>
                <Button variant="outline" className="gap-2" onClick={() => { setApprovalState('pending'); setApprovalError(null); }}>
                  Rescind
                </Button>
              </div>
            )}
            <Button variant="outline" className="gap-2" onClick={() => setShowPolicyModal(true)}>
              <FileText className="h-4 w-4" />
              View Policy
            </Button>
          </div>
          {approvalError && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-4 py-2.5 ring-1 ring-destructive/20">
              <XCircle className="h-4 w-4 text-destructive" />
              <span className="text-sm font-medium text-destructive">{approvalError}</span>
            </div>
          )}
        </section>

        {/* Timeline + Recovery Trace */}
        <section className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Investigation Timeline" description="Audit trail of decision events" />
            <AuditTimeline events={timeline} />
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Recovery Trace" description="Decision workflow at a glance" />
            <RecoveryTrace steps={recoveryTrace} currentStep={approvalState === 'pending' ? 4 : (approvalState === 'requested' ? 5 : 6)} />
          </div>
        </section>

        {/* Policy Modal */}
        <Dialog open={showPolicyModal} onOpenChange={setShowPolicyModal}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Merchant Recovery Policy</DialogTitle>
              <DialogDescription>
                Detailed rules for automatic recovery execution
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <span className="col-span-2 text-sm font-medium text-muted-foreground">Policy Version</span>
                <span className="col-span-2 text-sm font-medium">1.0</span>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <span className="col-span-2 text-sm font-medium text-muted-foreground">Max Auto Retries</span>
                <span className="col-span-2 text-sm font-medium">{policy.maxAutomaticRetries}</span>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <span className="col-span-2 text-sm font-medium text-muted-foreground">Max Auto Recovery</span>
                <span className="col-span-2 text-sm font-medium">{formatCurrency(policy.maxAutomaticRecoveryValue)}</span>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <span className="col-span-2 text-sm font-medium text-muted-foreground">Approval Threshold</span>
                <span className="col-span-2 text-sm font-medium">{formatCurrency(policy.humanApprovalAbove)}</span>
              </div>
              <div className="grid grid-cols-4 items-start gap-4">
                <span className="col-span-2 text-sm font-medium text-muted-foreground">Allowed Actions</span>
                <div className="col-span-2 flex flex-col gap-1">
                  {policy.allowedActions.map((action, i) => (
                     <span key={i} className="text-sm font-medium">{action}</span>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <span className="col-span-2 text-sm font-medium text-muted-foreground">Stop/Escalation Rules</span>
                <span className="col-span-2 text-sm font-medium">Escalate if transaction {'>'} {formatCurrency(policy.humanApprovalAbove)}</span>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <Button onClick={() => setShowPolicyModal(false)}>Close</Button>
            </div>
          </DialogContent>
        </Dialog>

        <div className="border-t border-border pt-4 text-[11px] text-muted-foreground">
          All figures are simulated demo data · Transaction ID: {payment.transactionId}
        </div>
          </>
        )}
      </PageContainer>
    </AppShell>
  );
}
