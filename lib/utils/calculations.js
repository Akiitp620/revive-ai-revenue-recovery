export function expectedRecovery(amount, probability) {
  return Math.round(amount * probability);
}

export function incrementalRecovery(reviveRecovered, baselineRecovered) {
  return reviveRecovered - baselineRecovered;
}

export function recoveryImprovement(reviveRecovered, baselineRecovered) {
  if (baselineRecovered === 0) return 0;
  return ((reviveRecovered - baselineRecovered) / baselineRecovered) * 100;
}

export function recoveryRate(recovered, totalAtRisk) {
  if (totalAtRisk === 0) return 0;
  return (recovered / totalAtRisk) * 100;
}
