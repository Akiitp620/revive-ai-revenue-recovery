'use client';

import { useEffect, useState } from 'react';
import { ArrowUpRight, CalendarDays, Download } from 'lucide-react';

import { getDashboardSummary } from '@/lib/api/dashboard';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { PageHeader } from '@/components/shared/page-header';
import { SectionHeader } from '@/components/shared/section-header';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { MetricCard } from '@/components/dashboard/metric-card';
import { RevenueTrendChart } from '@/components/charts/revenue-trend-chart';
import { PaymentHealth } from '@/components/dashboard/payment-health';
import { RecoveryQueue } from '@/components/dashboard/recovery-queue';
import { Button } from '@/components/ui/button';

export default function Home() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    getDashboardSummary()
      .then((data) => {
        if (active) setSummary(data);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, []);

  function retry() {
    setError(false);
    setSummary(null);
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError(true));
  }

  return (
    <AppShell>
      <PageContainer>
        <PageHeader
          title="Revenue Recovery Control Tower"
          subtitle="Monitor revenue at risk, recovery opportunities and incremental recovery performance."
        >
          <Button variant="outline" size="sm" className="gap-2">
            <CalendarDays className="h-3.5 w-3.5" />
            Last 30 days
          </Button>
          <Button variant="ghost" size="sm" className="hidden gap-2 sm:flex">
            <Download className="h-3.5 w-3.5" />
            Export
          </Button>
        </PageHeader>

        {error ? (
          <div className="rounded-xl border border-border bg-card">
            <ErrorState
              title="Unable to load dashboard data"
              description="The recovery summary could not be loaded. Please try again."
              onRetry={retry}
            />
          </div>
        ) : !summary ? (
          <LoadingSkeleton variant="cards" />
        ) : (
          <>
            <section aria-label="Key performance indicators" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Revenue at Risk" value={summary.kpis.revenueAtRisk} caption="Across failed payments" icon="risk" />
              <MetricCard label="Recoverable Revenue" value={summary.kpis.recoverableRevenue} caption="Estimated opportunity" icon="recoverable" />
              <MetricCard label="Revenue Recovered" value={summary.kpis.revenueRecovered} trend={12.4} trendLabel="vs previous period" icon="recovered" accent />
              <MetricCard label="Incremental Recovery" value={summary.kpis.incrementalRecovery} caption={summary.kpis.incrementalRecoveryLabel} icon="incremental" accent />
            </section>

            <section className="mt-8 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,1fr)]">
              <div className="rounded-xl border border-border bg-card p-5 lg:p-6">
                <SectionHeader
                  title="Revenue Recovery Trend"
                  description="Cumulative performance against a fixed retry baseline"
                  action={<span className="hidden items-center gap-1 text-xs text-success sm:flex"><ArrowUpRight className="h-3.5 w-3.5" /> 54.5% vs baseline</span>}
                />
                <RevenueTrendChart data={summary.revenueTrend} />
              </div>

              <div className="rounded-xl border border-border bg-card p-5 lg:p-6">
                <SectionHeader title="Payment Health" description="Success rate by payment method" />
                <PaymentHealth data={summary.paymentHealth} />
              </div>
            </section>

            <section className="mt-8 rounded-xl border border-border bg-card p-5 lg:p-6">
              <SectionHeader
                title="AI Recovery Queue"
                description="Highest-value recovery decisions requiring attention"
                action={<Button variant="ghost" size="sm" className="gap-1.5 text-xs text-primary">View all payments <ArrowUpRight className="h-3.5 w-3.5" /></Button>}
              />
              <RecoveryQueue data={summary.recoveryQueue} />
            </section>

            <div className="mt-6 flex items-center justify-between border-t border-border pt-4 text-[11px] text-muted-foreground">
              <span>All figures are simulated demo data</span>
              <span>Last updated just now</span>
            </div>
          </>
        )}
      </PageContainer>
    </AppShell>
  );
}
