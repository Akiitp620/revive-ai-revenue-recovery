import { dashboardSummary } from '@/lib/mock/dashboard';

const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getDashboardSummary() {
  await delay(SIMULATED_LATENCY);
  return dashboardSummary;
}

export async function getRevenueTrend() {
  await delay(SIMULATED_LATENCY);
  return dashboardSummary.revenueTrend;
}

export async function getPaymentHealth() {
  await delay(SIMULATED_LATENCY);
  return dashboardSummary.paymentHealth;
}

export async function getRecoveryQueue() {
  await delay(SIMULATED_LATENCY);
  return dashboardSummary.recoveryQueue;
}
