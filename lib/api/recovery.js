import { findInvestigation } from '@/lib/mock/investigations';

const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getRecoveryMetrics() {
  try {
    const res = await fetch('/api/v1/dashboard/overview');
    if (res.ok) {
      const data = await res.json();
      const kpis = data.kpis || {};

      const formatKpi = (val) => (val === undefined || val === null) ? 'N/A' : val;

      return {
        kpis: {
          revenueAtRisk: formatKpi(kpis.revenueAtRisk),
          recoverable: formatKpi(kpis.recoverableRevenue),
          recovered: formatKpi(kpis.revenueRecovered),
          incrementalRecovery: formatKpi(kpis.incrementalRecovery),
          incrementalRecoveryLabel: kpis.incrementalRecoveryLabel || 'vs baseline',
        },
        pipeline: data.pipeline || [],
        distribution: data.distribution || [],
        trend: data.revenueTrend || [],
        baselineComparison: data.baselineComparison || null,
        efficiency: data.efficiency || null,
        opportunities: data.opportunities || [],
        activity: data.activity || [],
        insight: data.insight || null,
        guardrails: data.guardrails || null,
        merchantPolicy: data.merchantPolicy ? {
          allowedActions: data.merchantPolicy.allowed_actions || [],
          humanApprovalAbove: data.merchantPolicy.human_approval_above || 0,
          version: data.merchantPolicy.version || 'Unknown'
        } : null
      };
    }
  } catch (error) {
    console.error('Failed to fetch recovery metrics', error);
  }
  return {
    kpis: { revenueAtRisk: 'N/A', recoverable: 'N/A', recovered: 'N/A', incrementalRecovery: 'N/A', incrementalRecoveryLabel: 'vs baseline' },
    pipeline: [],
    distribution: [],
    trend: [],
    baselineComparison: null,
    efficiency: null,
    opportunities: [],
    activity: [],
    insight: null,
    guardrails: null,
    merchantPolicy: null
  };
}

export async function getRecoveryPipeline() {
  const metrics = await getRecoveryMetrics();
  return metrics.pipeline;
}

export async function getRecoveryActions() {
  const metrics = await getRecoveryMetrics();
  return metrics.distribution;
}

export async function getRecoveryOpportunities() {
  const metrics = await getRecoveryMetrics();
  return metrics.opportunities;
}

export async function getRecoveryActivity() {
  const metrics = await getRecoveryMetrics();
  return metrics.activity;
}

const investigationMap = new Map();

export async function createOrGetInvestigationId(paymentId) {
  if (investigationMap.has(paymentId)) return investigationMap.get(paymentId);
  try {
    const res = await fetch('/api/v1/investigations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ payment_id: String(paymentId) }),
    });
    if (res.ok) {
      const data = await res.json();
      investigationMap.set(paymentId, data.investigation_id);
      return data.investigation_id;
    }
  } catch (error) {
    console.error('Failed to create investigation', error);
  }
  return paymentId; // fallback
}

export async function getRecoveryActionsForPayment(id) {
  try {
    const res = await fetch(`/api/v1/recovery/options/${id}`);
    if (res.ok) {
      const data = await res.json();
      const base = findInvestigation(id);
      return base.actions.filter(a => data.allowed_actions.includes(a.id));
    }
  } catch(e) {
     console.error(e);
  }
  await delay(SIMULATED_LATENCY);
  const investigation = findInvestigation(id);
  return investigation.actions;
}

export async function getInvestigation(id) {
  try {
    const invId = await createOrGetInvestigationId(id);
    const res = await fetch(`/api/v1/investigations/${invId}`);
    if (res.ok) {
      const data = await res.json();
      const base = findInvestigation(id);
      return {
        ...base,
        investigation_id: invId,
        actions: data.actions && data.actions.length > 0 ? data.actions : base.actions,
        recommendation: {
          ...base.recommendation,
          action: data.recommendation || base.recommendation.action,
          confidence: data.confidence ? Math.round(data.confidence * 100) : base.recommendation.confidence,
        },
      };
    }
  } catch (error) {
    console.error('Failed to fetch investigation', error);
  }
  await delay(SIMULATED_LATENCY);
  return findInvestigation(id);
}

export async function executeRecovery(paymentId, actionId) {
  const res = await fetch('/api/v1/recovery/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_id: String(paymentId), action: String(actionId) }),
  });
  const data = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
  if (!res.ok) {
    // Return the error body so the caller can surface it; include an explicit error field
    return { error: data.detail || data.error || `Request failed with status ${res.status}`, ...data };
  }
  return data;
}

export async function getAuditTimeline(id) {
  try {
    const invId = await createOrGetInvestigationId(id);
    const res = await fetch(`/api/v1/audit/${invId}`);
    if (res.ok) {
      const data = await res.json();
      return data.events;
    }
  } catch(error) {
    console.error('Failed to fetch audit timeline', error);
  }
  await delay(SIMULATED_LATENCY);
  const investigation = findInvestigation(id);
  return investigation.timeline;
}
