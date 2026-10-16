import { describe, expect, it } from 'vitest'
import { RansomwareApiError } from './ransomwareApi'
import { getRansomwareUiState } from './ransomwareUiState'
import type { RansomwareResult } from '../types/ransomware'

function baseResult(): RansomwareResult {
  return {
    schema_version: '1.0',
    task_id: 'RW-110-1',
    request_id: 'req-001',
    trace_id: 'trace-001',
    scenario_id: 'rw-attack-070891bdbaec',
    industry: 'energy',
    site_id: 'synthetic-site-001',
    site_type: 'control_centre',
    runtime_state: 'live_model',
    artifact_status: 'loaded',
    data_provenance: 'LIVE_MODEL',
    decision: 'investigate',
    recommended_actions: [],
    human_approval_required: true,
    real_action_executed: false,
    warnings: [],
    canonical_contract_complete: false,
  }
}

describe('RW-121-1 genuine backend failure contracts', () => {
  it.each([
    ['unavailable', 'UNAVAILABLE', 'backend_unavailable'],
    ['degraded', 'UNAVAILABLE', 'backend_unavailable'],
    ['fallback', 'FALLBACK', 'fallback_active'],
  ] as const)(
    'blocks a genuine %s response',
    (runtimeState, provenance, expectedState) => {
      const response = {
        state: runtimeState,
        runtime_state: runtimeState,
        decision: 'unavailable' as const,
        data_provenance: provenance,
        request_id: 'req-failure-001',
        trace_id: 'trace-failure-001',
        warnings: ['ML service unavailable'],
        fallback_is_live_inference: false as const,
        human_approval_required: true as const,
        real_action_executed: false as const,
      }

      const state = getRansomwareUiState(response)

      expect(state.id).toBe(expectedState)
      expect(state.blocking).toBe(true)
    },
  )

  it('shows ML timeout for a genuine unavailable response', () => {
    const response = {
      state: 'unavailable' as const,
      runtime_state: 'unavailable' as const,
      decision: 'unavailable' as const,
      data_provenance: 'UNAVAILABLE' as const,
      request_id: 'req-timeout-001',
      trace_id: 'trace-timeout-001',
      warnings: ['ML service timeout after retry policy'],
      fallback_is_live_inference: false as const,
      human_approval_required: true as const,
      real_action_executed: false as const,
    }

    const state = getRansomwareUiState(response)

    expect(state.id).toBe('ml_timeout')
    expect(state.blocking).toBe(true)
  })
})

describe('RW-121-1 dashboard failure states', () => {
  it('shows no model artifact', () => {
    const result: RansomwareResult = { ...baseResult(), artifact_status: 'missing' }
    expect(getRansomwareUiState(result).id).toBe('no_artifact')
  })

  it('shows feature mismatch', () => {
    const result: RansomwareResult = { ...baseResult(), artifact_status: 'incompatible' }
    expect(getRansomwareUiState(result).id).toBe('feature_mismatch')
  })

  it.each([
    'stale',
    'corrupt',
    'unavailable',
  ] as const)('blocks unsafe artifact status: %s', (status) => {
    const result: RansomwareResult = {
      ...baseResult(),
      artifact_status: status,
    }

    const state = getRansomwareUiState(result)

    expect(state.id).toBe('no_artifact')
    expect(state.blocking).toBe(true)
    expect(state.label).toBe('MODEL ARTIFACT UNAVAILABLE')
    expect(state.detail).toContain(status)
  })

  it('shows stale or missing calibration', () => {
    const result: RansomwareResult = {
      ...baseResult(),
      warnings: ['Calibration stale/missing; calibrated confidence blocked.'],
    }
    expect(getRansomwareUiState(result).id).toBe('calibration_stale')
  })

  it('shows backend unavailable', () => {
    const error = new RansomwareApiError('Backend unavailable.', 'network')
    expect(getRansomwareUiState(null, error).id).toBe('backend_unavailable')
  })

  it('shows ML timeout', () => {
    const error = new RansomwareApiError(
      'Backend request timed out.',
      'timeout',
    )
    expect(getRansomwareUiState(null, error).id).toBe('ml_timeout')
  })

  it('shows partial sources', () => {
    const result: RansomwareResult = {
      ...baseResult(),
      warnings: ['Partial sources: temporal challenger unavailable.'],
    }
    expect(getRansomwareUiState(result).id).toBe('partial_sources')
  })

  it('shows prohibited scenario', () => {
    const result: RansomwareResult = {
      ...baseResult(),
      warnings: ['Scenario prohibited: not permitted synthetic mode.'],
    }
    expect(getRansomwareUiState(result).id).toBe('scenario_prohibited')
  })

  it('shows fallback active', () => {
    const result: RansomwareResult = {
      ...baseResult(),
      runtime_state: 'fallback',
      data_provenance: 'FALLBACK',
    }
    expect(getRansomwareUiState(result).id).toBe('fallback_active')
  })

  it('shows ML timeout returned by the backend degradation contract', () => {
    const result: RansomwareResult = {
      ...baseResult(),
      runtime_state: 'unavailable',
      decision: 'unavailable',
      data_provenance: 'UNAVAILABLE',
      warnings: ['ML service timeout after retry policy'],
    }
    expect(getRansomwareUiState(result).id).toBe('ml_timeout')
  })

  it('shows backend unavailable for a generic unavailable result', () => {
    const result: RansomwareResult = {
      ...baseResult(),
      runtime_state: 'unavailable',
      decision: 'unavailable',
      data_provenance: 'UNAVAILABLE',
      warnings: ['ML service dependency unavailable'],
    }
    expect(getRansomwareUiState(result).id).toBe('backend_unavailable')
  })
})
