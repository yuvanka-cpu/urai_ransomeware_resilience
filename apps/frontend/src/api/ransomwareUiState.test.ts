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

describe('RW-121-1 dashboard failure states', () => {
  it('shows no model artifact', () => {
    const result: RansomwareResult = { ...baseResult(), artifact_status: 'missing' }
    expect(getRansomwareUiState(result).id).toBe('no_artifact')
  })

  it('shows feature mismatch', () => {
    const result: RansomwareResult = { ...baseResult(), artifact_status: 'incompatible' }
    expect(getRansomwareUiState(result).id).toBe('feature_mismatch')
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
})
