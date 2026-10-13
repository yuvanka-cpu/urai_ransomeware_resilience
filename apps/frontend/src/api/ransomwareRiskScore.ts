/**
 * Formats calibrated attack probability as a probability-based
 * 0–100 indicator.
 *
 * This is not an independent operational risk assessment.
 */
export function formatAttackRiskScore(
  calibratedProbability: number | null | undefined,
): string {
  if (
    typeof calibratedProbability !== 'number' ||
    !Number.isFinite(calibratedProbability) ||
    calibratedProbability < 0 ||
    calibratedProbability > 1
  ) {
    return 'Unavailable'
  }

  return `${(calibratedProbability * 100).toFixed(1)}/100`
}
