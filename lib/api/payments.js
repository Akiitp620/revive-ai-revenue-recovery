import { payments, findPayment } from '@/lib/mock/payments';

const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getPayments() {
  await delay(SIMULATED_LATENCY);
  return payments;
}

export async function getPayment(id) {
  await delay(SIMULATED_LATENCY);
  return findPayment(id);
}
