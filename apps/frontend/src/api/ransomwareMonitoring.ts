/** Read-only access to offline synthetic monitoring evidence. */

const API_BASE_URL =
  import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

const DATA_DRIFT_URL =
  `${API_BASE_URL}/api/v1/ransomware/monitoring/data-drift`

export type DataDriftReport = {
  status: 'drift_detected' | 'no_drift_detected' | 'unavailable'
  analysis_type: 'offline_synthetic_feature_distribution_comparison'
  data_provenance: 'synthetic_development'
  is_live_monitoring: false
  reason?: string
  reference_split?: string
  comparison_split?: string
  reference_count?: number
  current_count?: number
  threshold?: number
  feature_psi?: Record<string, number>
  drifted_features?: string[]
  interpretation_warning?: string
}

function unavailable(reason: string): DataDriftReport {
  return {
    status: 'unavailable',
    analysis_type: 'offline_synthetic_feature_distribution_comparison',
    data_provenance: 'synthetic_development',
    is_live_monitoring: false,
    reason,
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function validateDataDriftReport(value: unknown): DataDriftReport {
  if (!isRecord(value)) {
    return unavailable('Monitoring response is not an object.')
  }

  if (
    value.analysis_type !==
      'offline_synthetic_feature_distribution_comparison' ||
    value.data_provenance !== 'synthetic_development' ||
    value.is_live_monitoring !== false
  ) {
    return unavailable('Monitoring provenance is invalid.')
  }

  if (value.status === 'unavailable') {
    return unavailable(
      typeof value.reason === 'string'
        ? value.reason
        : 'Monitoring evidence is unavailable.',
    )
  }

  if (
    value.status !== 'drift_detected' &&
    value.status !== 'no_drift_detected'
  ) {
    return unavailable('Monitoring status is invalid.')
  }

  const psi = value.feature_psi
  const drifted = value.drifted_features
  const threshold = value.threshold

  if (
    value.reference_split !== 'train' ||
    value.comparison_split !== 'validation' ||
    value.reference_count !== 54 ||
    value.current_count !== 54 ||
    typeof threshold !== 'number' ||
    !Number.isFinite(threshold) ||
    threshold <= 0 ||
    !isRecord(psi) ||
    Object.keys(psi).length !== 54 ||
    !Array.isArray(drifted) ||
    !drifted.every((item) => typeof item === 'string')
  ) {
    return unavailable('Monitoring evidence contract is incomplete.')
  }

  const values = Object.values(psi)

  if (
    !values.every(
      (item) =>
        typeof item === 'number' &&
        Number.isFinite(item) &&
        item >= 0,
    )
  ) {
    return unavailable('Monitoring PSI values are invalid.')
  }

  const expectedDrifted = Object.entries(psi)
    .filter(([, item]) => (item as number) >= threshold)
    .map(([feature]) => feature)
    .sort()

  if (
    JSON.stringify(drifted) !== JSON.stringify(expectedDrifted) ||
    value.status !==
      (expectedDrifted.length ? 'drift_detected' : 'no_drift_detected')
  ) {
    return unavailable('Monitoring results are inconsistent.')
  }

  return value as DataDriftReport
}

export async function fetchDataDriftReport(
  timeoutMs = 2500,
): Promise<DataDriftReport> {
  const controller = new AbortController()
  const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(DATA_DRIFT_URL, {
      method: 'GET',
      signal: controller.signal,
    })

    if (!response.ok) {
      return unavailable(`Monitoring backend returned HTTP ${response.status}.`)
    }

    const payload: unknown = await response.json()
    return validateDataDriftReport(payload)
  } catch {
    return unavailable('Monitoring backend could not be reached.')
  } finally {
    globalThis.clearTimeout(timeout)
  }
}
