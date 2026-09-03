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

import { getInvestigation } from '@/lib/api/recovery';
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
import { formatCurrency, formatPercentage } from '@/lib/utils/formatting';

export default function PaymentInvestigationPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;

  const [investigation, setInvestigation] = useState(null);
  const [error, setError] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null);
  const [approvalState, setApprovalState] = useState('pending');

  useEffect(() => {
    let active = true;
    getInvestigation(id)
      .then((data) => {
        if (!active) return;
        setInvestigation(data);
        const recommended = data.actions.find((a) => a.recommended) || data.actions[0];
        setSelectedAction(recommended);
      })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [id]);

  function retry() {
    setError(false);
    setInvestigation(null);
    getInvestigation(id)
      .then((data) => {
        setInvestigation(data);
        const recommended = data.actions.find((a) => a.recommended) || data.actions[0];
        setSelectedAction(recommended);
      })
      .catch(() => setError(true));
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

  if (!investigation) {
    return (
      <AppShell>
        <PageContainer>
          <LoadingSkeleton variant="cards" />
        </PageContainer>
      </AppShell>
    );
  }

  const { diagnosis, customer, recovery, recommendation, actions, policy, timeline, recoveryTrace } = investigation;
  const amount = investigation.amount;

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
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">{investigation.transactionId}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{customer.name} · {investigation.paymentMethod}</p>
          </div>
          <div className="flex items-center gap-6">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Amount</p>
              <p className="text-2xl font-bold text-foreground tabular-nums">{formatCurrency(amount)}</p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Recovery Probability</p>
              <p className="text-2xl font-bold text-primary tabular-nums">{formatPercentage(recovery.probability)}</p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Expected Recovery</p>
              <p className="text-2xl font-bold text-success tabular-nums">{formatCurrency(recovery.expectedAmount)}</p>
            </div>
          </div>
        </div>

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
                <span className="text-sm font-bold text-success tabular-nums">{formatCurrency(selectedAction?.expectedRecovery)}</span>
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

        {/* Action Controls */}
        <section className="mb-8 flex flex-wrap items-center gap-3">
          {approvalState === 'pending' && (
            <Button
              className="gap-2"
              onClick={() => setApprovalState('requested')}
            >
              <Send className="h-4 w-4" />
              Request Approval
            </Button>
          )}
          {approvalState === 'requested' && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg bg-success/10 px-4 py-2.5 ring-1 ring-success/20">
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span className="text-sm font-medium text-success">Approval requested — pending review</span>
              </div>
              <Button variant="outline" className="gap-2" onClick={() => setApprovalState('pending')}>
                Rescind
              </Button>
            </div>
          )}
          <Button variant="outline" className="gap-2">
            <FileText className="h-4 w-4" />
            View Policy
          </Button>
        </section>

        {/* Timeline + Recovery Trace */}
        <section className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Investigation Timeline" description="Audit trail of decision events" />
            <AuditTimeline events={timeline} />
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <SectionHeader title="Recovery Trace" description="Decision workflow at a glance" />
            <RecoveryTrace steps={recoveryTrace} currentStep={5} />
          </div>
        </section>

        <div className="border-t border-border pt-4 text-[11px] text-muted-foreground">
          All figures are simulated demo data · Investigation ID: {investigation.transactionId}
        </div>
      </PageContainer>
    </AppShell>
  );
}
