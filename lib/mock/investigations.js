import { findPayment } from '@/lib/mock/payments';

export const investigationData = {
  'TXN-84291': {
    transactionId: 'TXN-84291',
    amount: 74500,
    currency: 'INR',
    status: 'FAILED_PAYMENT',
    paymentMethod: 'UPI',
    customer: {
      name: 'Arjun Mehta',
      id: 'CUST-3104',
      successfulPayments: 18,
      previousRecoveryRate: 81,
      averageTransaction: 32400,
      customerSince: '2024',
      segment: 'High Value',
    },
    diagnosis: {
      primary: 'Temporary issuer / payment degradation',
      evidence: [
        { label: 'Temporary failure pattern', detail: 'Issuer returned a transient error code' },
        { label: 'Only one previous attempt', detail: 'No retry fatigue detected' },
        { label: 'Strong customer payment history', detail: '18 successful payments in last 12 months' },
        { label: 'Similar cases recovered after delay', detail: '87% of comparable cases recovered within 48h' },
      ],
    },
    recovery: {
      probability: 82,
      expectedAmount: 61090,
    },
    recommendation: {
      action: 'Retry Later',
      confidence: 91,
      reasons: [
        'Highest expected recovery',
        'Temporary failure pattern',
        'Strong customer history',
        'Low previous retry count',
        'Allowed by merchant policy',
      ],
    },
    actions: [
      {
        id: 'RETRY_NOW',
        label: 'Retry Now',
        expectedRecovery: 48200,
        probability: 64,
        description: 'Immediately retry the same payment method',
      },
      {
        id: 'RETRY_LATER',
        label: 'Retry Later',
        expectedRecovery: 61090,
        probability: 82,
        description: 'Schedule a retry after a delay window',
        recommended: true,
      },
      {
        id: 'ALTERNATE_PAYMENT',
        label: 'Alternate Payment',
        expectedRecovery: 57800,
        probability: 78,
        description: 'Offer an alternative payment method',
      },
      {
        id: 'CUSTOMER_REMINDER',
        label: 'Customer Reminder',
        expectedRecovery: 41300,
        probability: 55,
        description: 'Send a payment reminder to the customer',
      },
      {
        id: 'STOP',
        label: 'Stop',
        expectedRecovery: 0,
        probability: 0,
        description: 'Stop recovery attempts for this payment',
      },
    ],
    policy: {
      maxAutomaticRetries: 2,
      maxAutomaticRecoveryValue: 50000,
      humanApprovalAbove: 50000,
      allowedActions: ['Retry', 'Alternate Payment', 'Reminder'],
      allowed: false,
      requiresApproval: true,
      reason: 'Transaction exceeds automatic recovery threshold',
    },
    blockingFactors: [
      'Transaction exceeds automatic recovery limit',
      'Merchant approval is required',
    ],
    supportingFactors: [
      'Recovery probability is strong',
      'Customer history is healthy',
    ],
    timeline: [
      { time: '14:21:04', event: 'Payment loaded', status: 'done' },
      { time: '14:21:05', event: 'Failure diagnosed', status: 'done' },
      { time: '14:21:06', event: 'Customer context checked', status: 'done' },
      { time: '14:21:06', event: 'Recovery probability calculated', status: 'done' },
      { time: '14:21:07', event: 'Recovery options evaluated', status: 'done' },
      { time: '14:21:07', event: 'Retry Later selected', status: 'done' },
      { time: '14:21:07', event: 'Merchant policy evaluated', status: 'done' },
      { time: '14:21:08', event: 'Human approval requested', status: 'current' },
    ],
    recoveryTrace: [
      'Detection',
      'Diagnosis',
      'Prediction',
      'Action Comparison',
      'Policy',
      'Approval',
      'Outcome',
    ],
  },
};

export function findInvestigation(id) {
  if (investigationData[id]) return investigationData[id];
  const payment = findPayment(id);
  return {
    ...investigationData['TXN-84291'],
    transactionId: payment.transactionId,
    amount: payment.amount,
    paymentMethod: payment.paymentMethod,
    customer: {
      ...investigationData['TXN-84291'].customer,
      name: payment.customer,
      id: payment.customerId,
    },
    diagnosis: {
      primary: payment.failureReason,
      evidence: [
        { label: 'Failure pattern analyzed', detail: `${payment.attempts} previous attempt(s)` },
        { label: 'Payment method', detail: payment.paymentMethod },
        { label: 'Recovery probability assessed', detail: `${payment.recoveryProbability}% likelihood` },
        { label: 'Recommended action', detail: payment.recommendedAction },
      ],
    },
    recovery: {
      probability: payment.recoveryProbability,
      expectedAmount: payment.expectedRecovery,
    },
    recommendation: {
      action: payment.recommendedAction,
      confidence: Math.round(payment.recoveryProbability * 1.1),
      reasons: [
        'Highest expected recovery under policy',
        'Failure pattern analyzed',
        'Customer context evaluated',
        'Merchant policy checked',
      ],
    },
    actions: [
      { id: 'RETRY_NOW', label: 'Retry Now', expectedRecovery: Math.round(payment.amount * 0.64), probability: 64, description: 'Immediately retry the same payment method' },
      { id: 'RETRY_LATER', label: 'Retry Later', expectedRecovery: payment.expectedRecovery, probability: payment.recoveryProbability, description: 'Schedule a retry after a delay window', recommended: true },
      { id: 'ALTERNATE_PAYMENT', label: 'Alternate Payment', expectedRecovery: Math.round(payment.amount * 0.76), probability: 76, description: 'Offer an alternative payment method' },
      { id: 'CUSTOMER_REMINDER', label: 'Customer Reminder', expectedRecovery: Math.round(payment.amount * 0.52), probability: 52, description: 'Send a payment reminder to the customer' },
      { id: 'STOP', label: 'Stop', expectedRecovery: 0, probability: 0, description: 'Stop recovery attempts for this payment' },
    ],
    policy: investigationData['TXN-84291'].policy,
    blockingFactors: payment.amount > 50000
      ? ['Transaction exceeds automatic recovery limit', 'Merchant approval is required']
      : [],
    supportingFactors: ['Recovery probability is strong', 'Customer history is healthy'],
    timeline: [
      { time: '14:21:04', event: 'Payment loaded', status: 'done' },
      { time: '14:21:05', event: 'Failure diagnosed', status: 'done' },
      { time: '14:21:06', event: 'Customer context checked', status: 'done' },
      { time: '14:21:06', event: 'Recovery probability calculated', status: 'done' },
      { time: '14:21:07', event: 'Recovery options evaluated', status: 'done' },
      { time: '14:21:07', event: `${payment.recommendedAction} selected`, status: 'done' },
      { time: '14:21:07', event: 'Merchant policy evaluated', status: 'done' },
      { time: '14:21:08', event: 'Human approval requested', status: 'current' },
    ],
    recoveryTrace: ['Detection', 'Diagnosis', 'Prediction', 'Action Comparison', 'Policy', 'Approval', 'Outcome'],
  };
}
