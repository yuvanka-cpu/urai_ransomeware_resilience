import { describe, expect, it } from 'vitest'
import {
  formatForensicSignal,
  getForensicSignals,
} from './ransomwareForensicEvidence'
import type { RansomwareResult } from '../types/ransomware'

describe('formatForensicSignal', () => {
  it.each([
    [0, '0.0%'],
    [0.43, '43.0%'],
    [1, '100.0%'],
  ])('formats %s as %s', (input, expected) => {
    expect(formatForensicSignal(input)).toBe(expected)
  })

  it.each([null, undefined, -0.1, 1.1, Number.NaN, Infinity])(
    'returns Unavailable for invalid input %s',
    (input) => {
      expect(formatForensicSignal(input)).toBe('Unavailable')
    },
  )
})

describe('getForensicSignals', () => {
  it('returns unavailable values when no result exists', () => {
    expect(getForensicSignals(null)).toEqual([
      { label: 'Rule signal', value: 'Unavailable' },
      { label: 'Anomaly signal', value: 'Unavailable' },
      { label: 'Graph signal', value: 'Unavailable' },
      { label: 'CatBoost signal', value: 'Unavailable' },
    ])
  })

  it('formats available component scores', () => {
    const result = {
      model_result: {
        components: {
          rule_score: 0.1,
          anomaly_score: 0.2,
          graph_score: 0.3,
          catboost_score: 0.4,
        },
      },
    } as RansomwareResult

    expect(getForensicSignals(result)).toEqual([
      { label: 'Rule signal', value: '10.0%' },
      { label: 'Anomaly signal', value: '20.0%' },
      { label: 'Graph signal', value: '30.0%' },
      { label: 'CatBoost signal', value: '40.0%' },
    ])
  })
})
