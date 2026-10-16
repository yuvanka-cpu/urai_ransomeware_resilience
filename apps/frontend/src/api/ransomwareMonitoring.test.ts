import { describe, expect, it } from 'vitest'
import { validateDataDriftReport } from './ransomwareMonitoring'

const validReport = {
  status: 'drift_detected',
  analysis_type: 'offline_synthetic_feature_distribution_comparison',
  data_provenance: 'synthetic_development',
  is_live_monitoring: false,
  reference_split: 'train',
  comparison_split: 'validation',
  reference_count: 54,
  current_count: 54,
  threshold: 0.2,
  feature_psi: {
    ...Object.fromEntries(
      Array.from({ length: 52 }, (_, index) => [`feature_${index}`, 0.01]),
    ),
    observable_value_max: 0.5768,
    remote_admin_peer_count: 0.2182,
  },
  drifted_features: [
    'observable_value_max',
    'remote_admin_peer_count',
  ],
}

describe('RW-130-1 frontend monitoring validation', () => {
  it('accepts valid offline synthetic drift evidence', () => {
    const result = validateDataDriftReport(validReport)

    expect(result.status).toBe('drift_detected')
    expect(result.is_live_monitoring).toBe(false)
    expect(result.drifted_features).toHaveLength(2)
  })

  it('rejects evidence claiming live monitoring', () => {
    const result = validateDataDriftReport({
      ...validReport,
      is_live_monitoring: true,
    })

    expect(result.status).toBe('unavailable')
  })

  it('rejects inconsistent drift results', () => {
    const result = validateDataDriftReport({
      ...validReport,
      drifted_features: [],
    })

    expect(result.status).toBe('unavailable')
  })

  it('rejects invalid PSI values', () => {
    const result = validateDataDriftReport({
      ...validReport,
      feature_psi: {
        ...validReport.feature_psi,
        observable_value_max: -1,
      },
    })

    expect(result.status).toBe('unavailable')
  })

  it('preserves unavailable monitoring status', () => {
    const result = validateDataDriftReport({
      status: 'unavailable',
      analysis_type: 'offline_synthetic_feature_distribution_comparison',
      data_provenance: 'synthetic_development',
      is_live_monitoring: false,
      reason: 'Report missing.',
    })

    expect(result.status).toBe('unavailable')
    expect(result.reason).toBe('Report missing.')
  })
})
