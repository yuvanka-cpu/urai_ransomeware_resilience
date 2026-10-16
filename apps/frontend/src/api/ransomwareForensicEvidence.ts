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

export interface ForensicInterpretation {
  signal: string
  interpretation: string
  investigation: string
}

export function getForensicInterpretations(
  result: RansomwareResult | null,
): ForensicInterpretation[] {
  if (
    !result ||
    result.runtime_state !== 'live_model' ||
    result.artifact_status !== 'loaded' ||
    result.data_provenance !== 'LIVE_MODEL' ||
    result.decision === 'unavailable' ||
    result.model_result?.runtime_contract?.synthetic_only !== true ||
    result.model_result.runtime_contract.real_action_executed !== false
  ) {
    return []
  }

  const components = result.model_result.components

  const definitions = [
    {
      key: 'rule_score',
      signal: 'Rule-based evidence',
      interpretation: 'A rule-based detection component produced a score.',
      investigation: 'Review the underlying synthetic event records and applicable detection rules.',
    },
    {
      key: 'anomaly_score',
      signal: 'Anomaly evidence',
      interpretation: 'The anomaly component identified a scored deviation from its reference behaviour.',
      investigation: 'Review the observable features and baseline used for anomaly scoring.',
    },
    {
      key: 'graph_score',
      signal: 'Relationship evidence',
      interpretation: 'The graph component produced a relationship-based detection signal.',
      investigation: 'Review available asset relationships and dependency evidence. Propagation is not established.',
    },
    {
      key: 'catboost_score',
      signal: 'Classifier evidence',
      interpretation: 'The CatBoost classifier produced a detection score.',
      investigation: 'Compare the classifier output with other signals and available synthetic observations.',
    },
  ] as const

  return definitions
    .filter(({ key }) => {
      const value = components?.[key]
      return typeof value === 'number' &&
        Number.isFinite(value) &&
        value >= 0 &&
        value <= 1
    })
    .map(({ signal, interpretation, investigation }) => ({
      signal,
      interpretation,
      investigation,
    }))
}
