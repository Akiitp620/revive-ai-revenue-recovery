import { recoveryMetrics } from '@/lib/mock/recovery';
import { findInvestigation } from '@/lib/mock/investigations';

const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getRecoveryMetrics() {
  await delay(SIMULATED_LATENCY);
  return recoveryMetrics;
}

export async function getRecoveryPipeline() {
  await delay(SIMULATED_LATENCY);
  return recoveryMetrics.pipeline;
}

export async function getRecoveryActions() {
  await delay(SIMULATED_LATENCY);
  return recoveryMetrics.distribution;
}

export async function getRecoveryOpportunities() {
  await delay(SIMULATED_LATENCY);
  return recoveryMetrics.opportunities;
}

export async function getRecoveryActivity() {
  await delay(SIMULATED_LATENCY);
  return recoveryMetrics.activity;
}

export async function getRecoveryActionsForPayment(id) {
  await delay(SIMULATED_LATENCY);
  const investigation = findInvestigation(id);
  return investigation.actions;
}

export async function getInvestigation(id) {
  await delay(SIMULATED_LATENCY);
  return findInvestigation(id);
}

export async function getAuditTimeline(id) {
  await delay(SIMULATED_LATENCY);
  const investigation = findInvestigation(id);
  return investigation.timeline;
}
