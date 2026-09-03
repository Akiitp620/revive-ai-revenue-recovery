export const NAV_ITEMS = [
  { label: 'Overview', href: '/', icon: 'LayoutDashboard' },
  { label: 'Payments', href: '/payments', icon: 'CreditCard' },
  { label: 'Recovery', href: '/recovery', icon: 'RefreshCw' },
  { label: 'Evaluation', href: '/evaluation', icon: 'BarChart3' },
];

export const BOTTOM_NAV_ITEMS = [
  { label: 'Settings', href: '/settings', icon: 'Settings' },
  { label: 'Help & Docs', href: '/docs', icon: 'BookOpen' },
];

export const RECOVERY_STATUS = {
  READY: { label: 'Ready', variant: 'success' },
  AWAITING_APPROVAL: { label: 'Awaiting Approval', variant: 'warning' },
  EXECUTING: { label: 'Executing', variant: 'info' },
  RECOVERED: { label: 'Recovered', variant: 'success' },
  STOPPED: { label: 'Stopped', variant: 'destructive' },
  ESCALATED: { label: 'Escalated', variant: 'warning' },
  DIAGNOSING: { label: 'Diagnosing', variant: 'info' },
};

export const RECOVERY_ACTIONS = {
  RETRY_NOW: 'Retry Now',
  RETRY_LATER: 'Retry Later',
  ALTERNATE_PAYMENT: 'Alternate Payment',
  CUSTOMER_REMINDER: 'Customer Reminder',
  STOP: 'Stop',
};

export const FAILURE_REASONS = {
  TEMPORARY_DECLINE: 'Temporary Decline',
  PAYMENT_METHOD_ISSUE: 'Payment Method Issue',
  REPEATED_FAILURE: 'Repeated Failure',
  HARD_DECLINE: 'Hard Decline',
  INSUFFICIENT_FUNDS: 'Insufficient Funds',
  UNKNOWN: 'Unknown Failure',
};

export const PAYMENT_METHODS = {
  UPI: 'UPI',
  CARD: 'Cards',
  NETBANKING: 'Netbanking',
  WALLET: 'Wallet',
};

export const MERCHANT = {
  name: 'DemoMart',
  environment: 'SIMULATION',
  status: 'Operational',
};
