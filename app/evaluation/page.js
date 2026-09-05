'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { PageHeader } from '@/components/shared/page-header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Info, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function EvaluationPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/v1/evaluations/latest')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch evaluation metrics');
        return res.json();
      })
      .then((d) => {
        if (d.sample_count === 0) {
          setData(null);
        } else {
          setData(d);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <AppShell>
        <PageContainer>
          <PageHeader
            title="Evaluation Engine"
            subtitle="Benchmark performance against held-out synthetic data."
          />
          <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
            <p className="text-muted-foreground animate-pulse">Loading evaluation results...</p>
          </div>
        </PageContainer>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <PageContainer>
          <PageHeader
            title="Evaluation Engine"
            subtitle="Benchmark performance against held-out synthetic data."
          />
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error Loading Evaluation</AlertTitle>
            <AlertDescription>
              {error}. Ensure the backend is running and the database is accessible.
            </AlertDescription>
          </Alert>
        </PageContainer>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <PageContainer>
          <PageHeader
            title="Evaluation Engine"
            subtitle="Benchmark performance against held-out synthetic data."
          />
          <Alert>
            <Info className="h-4 w-4" />
            <AlertTitle>No Evaluation Available</AlertTitle>
            <AlertDescription>
              There are no held-out evaluation results present in the database.
              Run the evaluation script `python scripts/evaluate.py` to generate the benchmark.
            </AlertDescription>
          </Alert>
        </PageContainer>
      </AppShell>
    );
  }

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };
  const formatPercent = (val) => {
    if (val === null || val === undefined) return 'N/A';
    return (val * 100).toFixed(1) + '%';
  };

  const chartData = [
    {
      name: 'Baseline',
      revenue: data.baseline_recovered_revenue ?? 0,
      fill: 'hsl(var(--muted-foreground))'
    },
    {
      name: 'REVIVE',
      revenue: data.revive_recovered_revenue ?? 0,
      fill: 'hsl(var(--primary))'
    }
  ];

  return (
    <AppShell>
      <PageContainer>
        <div className="flex flex-col gap-6">
          {/* 1. Benchmark Header */}
          <div className="space-y-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Synthetic Held-Out Benchmark</h1>
              <p className="text-muted-foreground mt-2">
                Measuring REVIVE&apos;s decision-making against the fixed-retry baseline on {data.sample_count} independent cases.
              </p>
            </div>

            <Alert className="bg-muted/50 border-primary/20">
              <Info className="h-4 w-4 text-primary" />
              <AlertTitle className="text-primary font-semibold">Important Methodology Note</AlertTitle>
              <AlertDescription className="text-muted-foreground mt-1">
                Results are computed on the <strong>{data.dataset_name || 'held-out'}</strong> synthetic dataset and are not production revenue.
                The baseline represents an existing fixed retry policy. REVIVE selects a policy-permitted recovery action using model/simulator outputs, and the revenue outcomes are entirely simulated based on the synthetic ground truth.
              </AlertDescription>
            </Alert>
          </div>

          {/* 2. Primary Business Outcome */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="md:col-span-2 bg-primary/5 border-primary/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium uppercase tracking-wider text-primary">Incremental Recovered Revenue</CardTitle>
                <CardDescription>Value added by REVIVE</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-primary">{formatCurrency(data.incremental_recovered_revenue)}</span>
                  <span className={`text-lg font-medium ${(data.improvement_percentage ?? 0) > 0 ? 'text-green-500' : (data.improvement_percentage ?? 0) < 0 ? 'text-destructive' : 'text-muted-foreground'}`}>
                    {data.improvement_percentage != null ? (data.improvement_percentage > 0 ? '+' : '') + formatPercent(data.improvement_percentage / 100) : 'N/A'}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">REVIVE Revenue</CardTitle>
                <CardDescription>Expected with AI Agent</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-3xl font-bold">{formatCurrency(data.revive_recovered_revenue)}</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">Baseline Revenue</CardTitle>
                <CardDescription>Fixed Retry Policy</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-3xl font-bold">{formatCurrency(data.baseline_recovered_revenue)}</span>
              </CardContent>
            </Card>
          </div>

          {/* 8. Comparison Visualization */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue Comparison</CardTitle>
              <CardDescription>Simulated recovery outcomes on {data.sample_count} cases</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <YAxis
                      stroke="hsl(var(--muted-foreground))"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(val) => `$${(val/1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(val) => formatCurrency(val)}
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
                      itemStyle={{ color: 'hsl(var(--foreground))' }}
                    />
                    <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            {/* 3. Recovery Performance */}
            <Card>
              <CardHeader>
                <CardTitle>Recovery Performance</CardTitle>
                <CardDescription>Agent efficiency and impact</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground">REVIVE Recovery Rate</span>
                  <span className="font-semibold text-lg">{formatPercent(data.recovery_rate)}</span>
                </div>
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground">Unnecessary Intervention Rate</span>
                  <span className="font-semibold text-lg">{formatPercent(data.unnecessary_intervention_rate)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Escalation Rate</span>
                  <span className="font-semibold text-lg">{formatPercent(data.escalation_rate)}</span>
                </div>
              </CardContent>
            </Card>

            {/* 4. Decision Quality */}
            <Card>
              <CardHeader>
                <CardTitle>Decision Quality</CardTitle>
                <CardDescription>Accuracy against synthetic ground truth</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground">Action-Selection Accuracy</span>
                  <span className="font-semibold text-lg">{formatPercent(data.action_selection_accuracy)}</span>
                </div>
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground">Root-Cause Accuracy</span>
                  <span className="font-semibold text-lg">{formatPercent(data.root_cause_accuracy)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Average Selection Gap</span>
                  <span className="font-semibold text-lg">{formatCurrency(data.average_selection_gap)}</span>
                </div>
              </CardContent>
            </Card>

            {/* 5. Governance / Safety */}
            <Card>
              <CardHeader>
                <CardTitle>Governance & Safety</CardTitle>
                <CardDescription>Adherence to deterministic policies</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground flex items-center gap-2">
                    Stop-Rule Compliance
                  </span>
                  <div className="flex items-center gap-2">
                    {(data.stop_rule_compliance === 1.0) && <ShieldCheck className="h-4 w-4 text-green-500" />}
                    <span className={`font-semibold text-lg ${data.stop_rule_compliance === 1.0 ? 'text-green-500' : (data.stop_rule_compliance != null ? 'text-destructive' : 'text-muted-foreground')}`}>
                      {formatPercent(data.stop_rule_compliance)}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Policy Violations</span>
                  <div className="flex items-center gap-2">
                    {(data.policy_violations === 0.0) && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                    <span className={`font-semibold text-lg ${data.policy_violations === 0.0 ? 'text-green-500' : (data.policy_violations != null ? 'text-destructive' : 'text-muted-foreground')}`}>
                      {formatPercent(data.policy_violations)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 6. Reliability */}
            <Card>
              <CardHeader>
                <CardTitle>Reliability</CardTitle>
                <CardDescription>Execution and tool robustness</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground">Tool Success Rate</span>
                  <span className={`font-semibold text-lg ${data.tool_success_rate === 1.0 ? 'text-green-500' : ''}`}>
                    {formatPercent(data.tool_success_rate)}
                  </span>
                </div>
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="text-muted-foreground">Average Decision Latency</span>
                  <span className="font-semibold text-lg">{data.average_decision_latency != null ? data.average_decision_latency.toFixed(3) + 's' : 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Evaluation Failures</span>
                  <span className="font-semibold text-lg">{data.evaluation_failures != null ? data.evaluation_failures : 'N/A'}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 10. Traceability */}
          <div className="flex justify-between items-center text-xs text-muted-foreground px-2 py-4 border-t border-border mt-4">
            <div className="flex gap-4">
              <span><strong>Dataset:</strong> {data.dataset_name || 'unknown'}</span>
              <span><strong>Samples:</strong> {data.sample_count != null ? data.sample_count : 'N/A'}</span>
              <span><strong>Model Version:</strong> {data.model_version || 'N/A'}</span>
            </div>
            <div>
              <span>Generated via Evaluation Engine</span>
            </div>
          </div>

        </div>
      </PageContainer>
    </AppShell>
  );
}
