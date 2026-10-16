import { describe, expect, it } from 'vitest'
import {
  formatForensicSignal,
  getForensicSignals,
  getForensicInterpretations,
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

describe('getForensicInterpretations', () => {
  const validResult = {
    runtime_state: 'live_model',
    artifact_status: 'loaded',
    data_provenance: 'LIVE_MODEL',
    decision: 'investigate',
    model_result: {
      runtime_contract: {
        synthetic_only: true,
        human_approval_required: true,
        real_action_executed: false,
        operational_state_claimed: false,
        physical_safety_determination: 'not_determined',
      },
      components: {
        rule_score: 0.42,
        anomaly_score: 0.31,
        graph_score: 0.72,
        catboost_score: 0.46,
      },
    },
  } as RansomwareResult

  it('provides guidance for available model signals', () => {
    const interpretations = getForensicInterpretations(validResult)

    expect(interpretations).toHaveLength(4)
    expect(interpretations.map((item) => item.signal)).toEqual([
      'Rule-based evidence',
      'Anomaly evidence',
      'Relationship evidence',
      'Classifier evidence',
    ])
    expect(interpretations.every((item) => item.investigation.length > 0)).toBe(true)
  })

  it('excludes invalid and missing signals', () => {
    const result = {
      ...validResult,
      model_result: {
        ...validResult.model_result,
        components: {
          rule_score: 0.42,
          anomaly_score: Number.NaN,
          graph_score: 1.5,
        },
      },
    } as RansomwareResult

    expect(getForensicInterpretations(result)).toHaveLength(1)
  })

  it('does not interpret unavailable or fallback results', () => {
    expect(getForensicInterpretations(null)).toEqual([])

    const fallback = {
      ...validResult,
      runtime_state: 'fallback',
      data_provenance: 'FALLBACK',
    } as RansomwareResult

    expect(getForensicInterpretations(fallback)).toEqual([])
  })
})
