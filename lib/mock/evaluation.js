export const evaluationResults = {
  context: {
    dataset: '10,000 failed payment cases',
    testSet: '1,500 cases',
    method: 'Baseline vs REVIVE',
  },
  decisionQuality: [
    { label: 'Root Cause Accuracy', value: 92.8, status: 'passed' },
    { label: 'Action Selection Accuracy', value: 88.6, status: 'passed' },
    { label: 'Policy Compliance', value: 98.9, status: 'passed' },
    { label: 'Stopping Rule Compliance', value: 100, status: 'passed' },
  ],
  businessImpact: {
    baselineRecovered: 1210000,
    reviveRecovered: 1870000,
    incrementalRecovery: 660000,
    recoveryImprovement: 54.5,
  },
  testSuites: [
    { name: 'Normal Failures', cases: 320, passRate: 94.1, status: 'passed' },
    { name: 'Temporary Declines', cases: 280, passRate: 91.4, status: 'passed' },
    { name: 'Hard Declines', cases: 180, passRate: 86.7, status: 'passed' },
    { name: 'Repeated Failures', cases: 150, passRate: 83.3, status: 'passed' },
    { name: 'High-Value Payments', cases: 200, passRate: 89.5, status: 'passed' },
    { name: 'Unknown Failures', cases: 120, passRate: 78.3, status: 'warning' },
    { name: 'Missing Context', cases: 90, passRate: 75.6, status: 'warning' },
    { name: 'Policy Conflicts', cases: 160, passRate: 96.9, status: 'passed' },
  ],
  decisionQualityChart: [
    { metric: 'Recovery Rate', baseline: 37.1, revive: 57.4 },
    { metric: 'Revenue Recovered', baseline: 12.1, revive: 18.7 },
    { metric: 'Unnecessary Interventions', baseline: 42, revive: 11 },
    { metric: 'Avg Attempts', baseline: 2.8, revive: 1.4 },
  ],
  reliability: [
    { label: 'Tool Failure Handling', status: 'Passed' },
    { label: 'Unknown Context Handling', status: 'Passed' },
    { label: 'Stopping Rules', status: 'Passed' },
    { label: 'Merchant Policy Enforcement', status: 'Passed' },
    { label: 'Human Escalation', status: 'Passed' },
    { label: 'Prompt Injection Safety', status: 'Passed' },
  ],
};
