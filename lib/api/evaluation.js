import { evaluationResults } from '@/lib/mock/evaluation';

const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getEvaluationResults() {
  await delay(SIMULATED_LATENCY);
  return evaluationResults;
}
