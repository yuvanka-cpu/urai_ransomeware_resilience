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

export type EvidenceAvailability = {
  status: 'unavailable'
  reason: string
  is_live_monitoring: false
}

export type ModelDriftReport = EvidenceAvailability & {
  task_id: 'RW-130-2'
  analysis_type: 'offline_model_performance_comparison'
  drift_detected: null
  metric_changes: Record<string, never>
}

export type IncidentTimingReport = EvidenceAvailability & {
  task_id: 'RW-130-3'
  analysis_type: 'offline_incident_timing'
  metrics: Record<
    'mttd' | 'mean_response_time' | 'mean_recovery_time',
    { status: 'unavailable'; mean_minutes: null }
  >
}

function unavailableModelDrift(reason: string): ModelDriftReport {
  return {
    task_id: 'RW-130-2',
    status: 'unavailable',
    reason,
    is_live_monitoring: false,
    analysis_type: 'offline_model_performance_comparison',
    drift_detected: null,
    metric_changes: {},
  }
}

function unavailableIncidentTiming(reason: string): IncidentTimingReport {
  const metric = () => ({
    status: 'unavailable' as const,
    mean_minutes: null,
  })

  return {
    task_id: 'RW-130-3',
    status: 'unavailable',
    reason,
    is_live_monitoring: false,
    analysis_type: 'offline_incident_timing',
    metrics: {
      mttd: metric(),
      mean_response_time: metric(),
      mean_recovery_time: metric(),
    },
  }
}

export function validateModelDriftReport(value: unknown): ModelDriftReport {
  if (
    !isRecord(value) ||
    value.task_id !== 'RW-130-2' ||
    value.analysis_type !== 'offline_model_performance_comparison' ||
    value.status !== 'unavailable' ||
    value.is_live_monitoring !== false ||
    value.drift_detected !== null ||
    !isRecord(value.metric_changes) ||
    Object.keys(value.metric_changes).length !== 0 ||
    typeof value.reason !== 'string' ||
    !value.reason.trim()
  ) {
    return unavailableModelDrift('Valid model-drift evidence is unavailable.')
  }

  return value as ModelDriftReport
}

export function validateIncidentTimingReport(
  value: unknown,
): IncidentTimingReport {
  if (
    !isRecord(value) ||
    value.task_id !== 'RW-130-3' ||
    value.analysis_type !== 'offline_incident_timing' ||
    value.status !== 'unavailable' ||
    value.is_live_monitoring !== false ||
    typeof value.reason !== 'string' ||
    !value.reason.trim() ||
    !isRecord(value.metrics)
  ) {
    return unavailableIncidentTiming('Valid incident-timing evidence is unavailable.')
  }

  for (const name of ['mttd', 'mean_response_time', 'mean_recovery_time']) {
    const metric = value.metrics[name]
    if (
      !isRecord(metric) ||
      metric.status !== 'unavailable' ||
      metric.mean_minutes !== null
    ) {
      return unavailableIncidentTiming('Incident-timing metrics are invalid.')
    }
  }

  return value as IncidentTimingReport
}

async function fetchMonitoringEvidence<T>(
  endpoint: string,
  validate: (value: unknown) => T,
  fallback: (reason: string) => T,
): Promise<T> {
  const controller = new AbortController()
  const timeout = globalThis.setTimeout(() => controller.abort(), 2500)

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      signal: controller.signal,
    })

    if (!response.ok) {
      return fallback(`Monitoring backend returned HTTP ${response.status}.`)
    }

    return validate(await response.json())
  } catch {
    return fallback('Monitoring backend could not be reached.')
  } finally {
    globalThis.clearTimeout(timeout)
  }
}

export function fetchModelDriftReport(): Promise<ModelDriftReport> {
  return fetchMonitoringEvidence(
    '/api/v1/ransomware/monitoring/model-drift',
    validateModelDriftReport,
    unavailableModelDrift,
  )
}

export function fetchIncidentTimingReport(): Promise<IncidentTimingReport> {
  return fetchMonitoringEvidence(
    '/api/v1/ransomware/monitoring/incident-timing',
    validateIncidentTimingReport,
    unavailableIncidentTiming,
  )
}
