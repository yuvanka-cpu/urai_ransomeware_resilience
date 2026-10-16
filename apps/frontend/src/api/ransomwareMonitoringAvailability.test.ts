import { describe, expect, it } from 'vitest'
import {
  validateModelDriftReport,
  validateIncidentTimingReport,
} from './ransomwareMonitoring'

describe('RW-130-2 model drift availability', () => {
  const valid = {
    task_id: 'RW-130-2',
    status: 'unavailable',
    analysis_type: 'offline_model_performance_comparison',
    is_live_monitoring: false,
    drift_detected: null,
    metric_changes: {},
    reason: 'No verified chronological comparison dataset.',
  }

  it('accepts the evidence-safe unavailable response', () => {
    expect(validateModelDriftReport(valid)).toEqual(valid)
  })

  it('rejects unsupported drift claims', () => {
    const result = validateModelDriftReport({
      ...valid,
      status: 'drift_detected',
      drift_detected: true,
    })

    expect(result.status).toBe('unavailable')
    expect(result.drift_detected).toBeNull()
  })

  it('rejects fabricated metric changes', () => {
    const result = validateModelDriftReport({
      ...valid,
      metric_changes: { recall: -0.5 },
    })

    expect(result.metric_changes).toEqual({})
  })

  it('rejects live monitoring claims', () => {
    const result = validateModelDriftReport({
      ...valid,
      is_live_monitoring: true,
    })

    expect(result.is_live_monitoring).toBe(false)
  })
})

describe('RW-130-3 incident timing availability', () => {
  const unavailableMetric = {
    status: 'unavailable',
    mean_minutes: null,
  }

  const valid = {
    task_id: 'RW-130-3',
    status: 'unavailable',
    analysis_type: 'offline_incident_timing',
    is_live_monitoring: false,
    reason: 'Verified incident timestamps are unavailable.',
    metrics: {
      mttd: unavailableMetric,
      mean_response_time: unavailableMetric,
      mean_recovery_time: unavailableMetric,
    },
  }

  it('accepts the evidence-safe unavailable response', () => {
    expect(validateIncidentTimingReport(valid)).toEqual(valid)
  })

  it('rejects fabricated MTTD measurements', () => {
    const result = validateIncidentTimingReport({
      ...valid,
      metrics: {
        ...valid.metrics,
        mttd: { status: 'available', mean_minutes: 4.2 },
      },
    })

    expect(result.metrics.mttd.mean_minutes).toBeNull()
    expect(result.status).toBe('unavailable')
  })

  it('rejects fabricated recovery measurements', () => {
    const result = validateIncidentTimingReport({
      ...valid,
      metrics: {
        ...valid.metrics,
        mean_recovery_time: {
          status: 'available',
          mean_minutes: 12,
        },
      },
    })

    expect(result.metrics.mean_recovery_time.mean_minutes).toBeNull()
  })

  it('rejects invalid provenance', () => {
    const result = validateIncidentTimingReport({
      ...valid,
      is_live_monitoring: true,
    })

    expect(result.is_live_monitoring).toBe(false)
    expect(result.status).toBe('unavailable')
  })
})
