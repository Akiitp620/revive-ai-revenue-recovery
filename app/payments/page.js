'use client';

import { useEffect, useMemo, useState } from 'react';
import { ArrowUpDown } from 'lucide-react';

import { getPayments } from '@/lib/api/payments';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { PageHeader } from '@/components/shared/page-header';
import { FilterBar } from '@/components/payments/filter-bar';
import { PaymentTable } from '@/components/payments/payment-table';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { EmptyState } from '@/components/shared/empty-state';
import { Button } from '@/components/ui/button';

const DEFAULT_FILTERS = {
  search: '',
  status: 'all',
  method: 'all',
  failure: 'all',
  probability: 'all',
};

function matchesProbability(value, filter) {
  if (filter === 'all') return true;
  if (filter === 'high') return value >= 70;
  if (filter === 'medium') return value >= 40 && value < 70;
  if (filter === 'low') return value < 40;
  return true;
}

export default function PaymentsPage() {
  const [payments, setPayments] = useState(null);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    let active = true;
    getPayments()
      .then((data) => { if (active) setPayments(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  function retry() {
    setError(false);
    setPayments(null);
    getPayments()
      .then(setPayments)
      .catch(() => setError(true));
  }

  const hasActiveFilters = useMemo(() =>
    filters.search !== '' ||
    filters.status !== 'all' ||
    filters.method !== 'all' ||
    filters.failure !== 'all' ||
    filters.probability !== 'all'
  , [filters]);

  const filtered = useMemo(() => {
    if (!payments) return [];
    let result = payments.filter((p) => {
      const searchMatch = !filters.search ||
        p.transactionId.toLowerCase().includes(filters.search.toLowerCase()) ||
        p.customer.toLowerCase().includes(filters.search.toLowerCase());
      const statusMatch = filters.status === 'all' || p.status === filters.status;
      const methodMatch = filters.method === 'all' || p.paymentMethod === filters.method;
      const failureMatch = filters.failure === 'all' || p.failureReason === filters.failure;
      const probMatch = matchesProbability(p.recoveryProbability, filters.probability);
      return searchMatch && statusMatch && methodMatch && failureMatch && probMatch;
    });
    result = [...result].sort((a, b) =>
      sortDesc ? b.amount - a.amount : a.amount - b.amount
    );
    return result;
  }, [payments, filters, sortDesc]);

  return (
    <AppShell>
      <PageContainer>
        <PageHeader
          title="Revenue at Risk"
          subtitle="Analyze failed payments and identify the highest-value recovery opportunities."
        />

        {error ? (
          <div className="rounded-xl border border-border bg-card">
            <ErrorState
              title="Unable to load payment data"
              description="The payment list could not be loaded. Please try again."
              onRetry={retry}
            />
          </div>
        ) : !payments ? (
          <div className="rounded-xl border border-border bg-card p-5">
            <LoadingSkeleton variant="table" />
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="mb-5">
              <FilterBar
                filters={filters}
                onChange={setFilters}
                onClear={() => setFilters(DEFAULT_FILTERS)}
                hasActiveFilters={hasActiveFilters}
              />
            </div>

            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {filtered.length} {filtered.length === 1 ? 'payment' : 'payments'}
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                onClick={() => setSortDesc((v) => !v)}
              >
                <ArrowUpDown className="h-3.5 w-3.5" />
                Sort by amount {sortDesc ? '↓' : '↑'}
              </Button>
            </div>

            {filtered.length === 0 ? (
              <EmptyState
                title="No revenue-risk payments match your current filters."
                description="Try adjusting or clearing the filters to see more results."
                actionLabel="Clear filters"
                onAction={() => setFilters(DEFAULT_FILTERS)}
              />
            ) : (
              <PaymentTable data={filtered} />
            )}
          </div>
        )}
      </PageContainer>
    </AppShell>
  );
}
