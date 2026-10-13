import type { RansomwareResult } from '../types/ransomware'

export interface ForensicSignal {
  label: string
  value: string
}

export function formatForensicSignal(value: number | null | undefined): string {
  if (
    typeof value !== 'number' ||
    !Number.isFinite(value) ||
    value < 0 ||
    value > 1
  ) {
    return 'Unavailable'
  }

  return `${(value * 100).toFixed(1)}%`
}

export function getForensicSignals(
  result: RansomwareResult | null,
): ForensicSignal[] {
  const components = result?.model_result?.components

  return [
    { label: 'Rule signal', value: formatForensicSignal(components?.rule_score) },
    { label: 'Anomaly signal', value: formatForensicSignal(components?.anomaly_score) },
    { label: 'Graph signal', value: formatForensicSignal(components?.graph_score) },
    { label: 'CatBoost signal', value: formatForensicSignal(components?.catboost_score) },
  ]
}
