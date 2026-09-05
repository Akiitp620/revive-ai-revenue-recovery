'use client';

import { useEffect, useState } from 'react';
import { CalendarDays, Download, RefreshCw } from 'lucide-react';

import { getRecoveryMetrics } from '@/lib/api/recovery';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { PageHeader } from '@/components/shared/page-header';
import { SectionHeader } from '@/components/shared/section-header';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { EmptyState } from '@/components/shared/empty-state';
import { MetricCard } from '@/components/dashboard/metric-card';
import { RecoveryPipeline } from '@/components/recovery/recovery-pipeline';
import { RecoveryActionDistribution } from '@/components/charts/recovery-action-distribution';
import { RevenueTrendChart } from '@/components/charts/revenue-trend-chart';
import { BaselineComparison } from '@/components/recovery/baseline-comparison';
import { RecoveryEfficiency } from '@/components/recovery/recovery-efficiency';
import { RecoveryOpportunityTable } from '@/components/recovery/recovery-opportunity-table';
import { RecoveryActivity } from '@/components/recovery/recovery-activity';
import { RecoveryInsight } from '@/components/recovery/recovery-insight';
import { RecoveryGuardrails } from '@/components/recovery/recovery-guardrails';
import { MerchantControl } from '@/components/recovery/merchant-control';
import { Button } from '@/components/ui/button';

export default function RecoveryPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let active = true;
    getRecoveryMetrics()
      .then((data) => {
        if (!active) return;
        setMetrics(data);
        setLastUpdated(new Date());
      })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  function retry() {
    setError(false);
    setMetrics(null);
    getRecoveryMetrics()
      .then((data) => {
        setMetrics(data);
        setLastUpdated(new Date());
      })
      .catch(() => setError(true));
  }

  function refresh() {
    setMetrics(null);
    getRecoveryMetrics()
      .then((data) => {
        setMetrics(data);
        setLastUpdated(new Date());
      })
      .catch(() => setError(true));
  }

  return (
    <AppShell>
      <PageContainer>
        <PageHeader
          title="Recovery Operations"
          subtitle="Monitor active recovery workflows and measure how much revenue REVIVE recovers."
        >
          <Button variant="outline" size="sm" className="gap-2">
            <CalendarDays className="h-3.5 w-3.5" />
            Last 30 days
          </Button>
          <Button variant="ghost" size="sm" className="gap-2" onClick={refresh}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
          <Button variant="ghost" size="sm" className="hidden gap-2 sm:flex">
            <Download className="h-3.5 w-3.5" />
            Export
          </Button>
        </PageHeader>

        {error ? (
          <div className="rounded-xl border border-border bg-card">
            <ErrorState
              title="Unable to load recovery data"
              description="The recovery operations data could not be loaded. Please try again."
              onRetry={retry}
            />
          </div>
        ) : !metrics ? (
          <div className="space-y-6">
            <LoadingSkeleton variant="cards" />
            <LoadingSkeleton />
            <LoadingSkeleton />
          </div>
        ) : (
          <>
            {/* KPI Strip */}
            <section aria-label="Recovery KPIs" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Revenue at Risk" value={metrics.kpis.revenueAtRisk} caption="Across failed payments" icon="risk" />
              <MetricCard label="Recoverable Revenue" value={metrics.kpis.recoverable} caption="Estimated opportunity" icon="recoverable" />
              <MetricCard label="Revenue Recovered" value={metrics.kpis.recovered} caption="By REVIVE recovery engine" icon="recovered" accent />
              <MetricCard label="Incremental Recovery" value={metrics.kpis.incrementalRecovery} caption={metrics.kpis.incrementalRecoveryLabel} icon="incremental" accent />
            </section>

            {/* Recovery Pipeline */}
            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader title="Recovery Pipeline" description="Failed payments flowing through recovery stages" />
              <RecoveryPipeline stages={metrics.pipeline} />
            </section>

            {/* Action Distribution + Recovery Trend */}
            <section className="mt-8 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
              <div className="rounded-xl border border-border bg-card p-5 lg:p-6">
                <SectionHeader title="Recovery Actions" description="Distribution of recovery decisions" />
                <RecoveryActionDistribution data={metrics.distribution} />
              </div>
              <div className="rounded-xl border border-border bg-card p-5 lg:p-6">
                <SectionHeader title="Revenue Recovery Trend" description="At risk vs recovered vs baseline" />
                <RevenueTrendChart data={metrics.trend} />
              </div>
            </section>

            {/* Baseline vs REVIVE */}
            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader title="Does REVIVE Recover More Revenue?" description="Baseline vs decision-based recovery comparison" />
              {metrics.baselineComparison ? (
                <BaselineComparison data={metrics.baselineComparison} />
              ) : (
                <EmptyState title="Baseline comparison data is not available." />
              )}
            </section>

            {/* Recovery Efficiency */}
            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader title="Recovery Efficiency" description="Operational performance metrics" />
              {metrics.efficiency ? (
                <RecoveryEfficiency metrics={metrics.efficiency} />
              ) : (
                <EmptyState title="Efficiency metrics not available." />
              )}
            </section>

            {/* Top Recovery Opportunities */}
            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader title="Top Recovery Opportunities" description="Highest-value payments awaiting action" />
              {!metrics.opportunities || metrics.opportunities.length === 0 ? (
                <EmptyState title="No recovery opportunities available." />
              ) : (
                <RecoveryOpportunityTable data={metrics.opportunities} />
              )}
            </section>

            {/* Recent Recovery Activity */}
            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader title="Recent Recovery Activity" description="Latest recovery actions and outcomes" />
              {!metrics.activity || metrics.activity.length === 0 ? (
                <EmptyState title="No recent activity available." />
              ) : (
                <RecoveryActivity data={metrics.activity} />
              )}
            </section>

            {/* Insight + Guardrails */}
            <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
              <div className="rounded-xl border border-border bg-card p-5 lg:p-6">
                <SectionHeader title="REVIVE Insight" description="Embedded decision intelligence" />
                {metrics.insight ? (
                  <RecoveryInsight insight={metrics.insight} />
                ) : (
                  <EmptyState title="Insights not available." />
                )}
              </div>
              <div className="rounded-xl border border-border bg-card p-5 lg:p-6">
                <SectionHeader title="Recovery Guardrails" description="Bounded recovery rules" />
                {metrics.guardrails ? (
                  <RecoveryGuardrails rules={metrics.guardrails} />
                ) : (
                  <EmptyState title="Guardrails not available." />
                )}
              </div>
            </section>

            {/* Merchant Control */}
            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader title="Merchant Recovery Policy" description="Policy boundaries governing recovery actions" />
              {metrics.merchantPolicy ? (
                <MerchantControl policy={metrics.merchantPolicy} />
              ) : (
                <EmptyState title="Policy not available." />
              )}
            </section>

            <div className="mt-6 flex items-center justify-between border-t border-border pt-4 text-[11px] text-muted-foreground">
              <span>All figures are simulated demo data · SIMULATION mode</span>
              <span>Last updated {lastUpdated ? 'just now' : '—'}</span>
            </div>
          </>
        )}
      </PageContainer>
    </AppShell>
  );
}
