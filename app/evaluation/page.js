'use client';

import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { PageHeader } from '@/components/shared/page-header';

export default function EvaluationPage() {
  return (
    <AppShell>
      <PageContainer>
        <PageHeader
          title="Evaluation Lab"
          subtitle="Measure whether REVIVE makes better recovery decisions than a fixed recovery baseline."
        />
        <div className="rounded-xl border border-border bg-card p-8 text-sm text-muted-foreground">
          Evaluation benchmarking will be available in the next stage.
        </div>
      </PageContainer>
    </AppShell>
  );
}
