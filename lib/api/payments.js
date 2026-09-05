const SIMULATED_LATENCY = 300;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function mapPaymentResponse(p) {
  const failureEvent = (p.failure_events && p.failure_events.length > 0) ? p.failure_events[0] : null;
  const failureReason = failureEvent ? failureEvent.failure_reason : 'Unknown Error';

  return {
    transactionId: String(p.id),
    customer: 'Customer ' + p.customer_id,
    customerId: String(p.customer_id),
    amount: p.amount,
    currency: p.currency,
    paymentMethod: 'Cards', // Not modeled in DB
    failureReason: failureReason,
    failureCode: failureReason.toUpperCase().replace(/\s+/g, '_'),
    attempts: p.attempts ? p.attempts.length : 1,
    recoveryProbability: 75, // Static fallback if predictions not joined
    expectedRecovery: Math.round(p.amount * 0.75),
    recommendedAction: 'Retry Later',
    status: p.status,
    date: p.created_at,
  };
}

export async function getPayments() {
  try {
    const res = await fetch('/api/v1/payments');
    if (res.ok) {
      const data = await res.json();
      return data.items.map(mapPaymentResponse);
    }
  } catch (error) {
    console.error('Failed to fetch payments', error);
  }
  return [];
}

export async function getPayment(id) {
  try {
    const res = await fetch(`/api/v1/payments/${id}`);
    if (res.ok) {
      const data = await res.json();
      return mapPaymentResponse(data);
    }
  } catch (error) {
    console.error(`Failed to fetch payment ${id}`, error);
  }
  return null;
}
