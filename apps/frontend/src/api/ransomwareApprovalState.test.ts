import { describe, expect, it } from 'vitest'
import { getApprovalDisplayState } from './ransomwareApprovalState'
import type { RansomwareResult } from '../types/ransomware'

function validResult(): RansomwareResult {
  return {
    schema_version: '1.0',
    task_id: 'RW-120',
    request_id: 'req-test',
    trace_id: 'trace-test',
    scenario_id: 'synthetic-test',
    industry: 'energy',
    site_id: 'synthetic-energy-001',
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
    model_result: {
      bundle_version: 'rw0906_v2',
      task: 'ransomware_resilience',
      sector: 'energy',
      decision: 'investigate',
      probabilities: { calibrated: 0.42 },
      components: {},
      calibration: {},
      thresholds: {},
      runtime_contract: {
        synthetic_only: true,
        human_approval_required: true,
        real_action_executed: false,
        operational_state_claimed: false,
        physical_safety_determination: 'not_determined',
      },
    },
  }
}

describe('Approval display safety evidence', () => {
  it('does not claim verified runtime safety before inference', () => {
    const state = getApprovalDisplayState(null)
    expect(state.humanApproval).toBe('NOT VERIFIED')
    expect(state.realAction).toBe('NOT VERIFIED')
    expect(state.operationalState).toBe('NOT VERIFIED')
  })

  it('displays safety values from a valid live-model contract', () => {
    expect(getApprovalDisplayState(validResult())).toEqual({
      humanApproval: 'TRUE',
      realAction: 'FALSE',
      operationalState: 'FALSE',
      physicalSafety: 'NOT DETERMINED',
    })
  })

  it('blocks a missing nested runtime contract', () => {
    const result = validResult()
    result.model_result = undefined
    expect(getApprovalDisplayState(result).humanApproval).toBe('NOT VERIFIED')
  })

  it('blocks an incompatible artifact', () => {
    const result = validResult()
    result.artifact_status = 'incompatible'
    expect(getApprovalDisplayState(result).realAction).toBe('NOT VERIFIED')
  })

  it('blocks a mismatched nested approval flag', () => {
    const result = validResult()
    result.model_result!.runtime_contract.human_approval_required = false
    expect(getApprovalDisplayState(result).humanApproval).toBe('NOT VERIFIED')
  })
})
