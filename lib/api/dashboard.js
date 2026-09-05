const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getDashboardSummary() {
  try {
    const res = await fetch('/api/v1/dashboard/overview');
    if (res.ok) {
      const data = await res.json();
      return {
        kpis: data.kpis,
        revenueTrend: data.revenueTrend || [],
        paymentHealth: data.paymentHealth || [],
        recoveryQueue: data.recoveryQueue || []
      };
    }
  } catch (error) {
    console.error('Failed to fetch dashboard summary', error);
  }
  return { kpis: {}, revenueTrend: [], paymentHealth: [], recoveryQueue: [] };
}

export async function getRevenueTrend() {
  const summary = await getDashboardSummary();
  return summary.revenueTrend;
}

export async function getPaymentHealth() {
  const summary = await getDashboardSummary();
  return summary.paymentHealth;
}

export async function getRecoveryQueue() {
  const summary = await getDashboardSummary();
  return summary.recoveryQueue;
}
