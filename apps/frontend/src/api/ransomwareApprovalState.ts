import type { RansomwareResult } from '../types/ransomware'

export interface ApprovalDisplayState {
  humanApproval: string
  realAction: string
  operationalState: string
  physicalSafety: string
}

export function getApprovalDisplayState(
  result: RansomwareResult | null,
): ApprovalDisplayState {
  const contract = result?.model_result?.runtime_contract

  if (
    !result ||
    result.runtime_state !== 'live_model' ||
    result.artifact_status !== 'loaded' ||
    result.data_provenance !== 'LIVE_MODEL' ||
    result.human_approval_required !== true ||
    result.real_action_executed !== false ||
    !contract ||
    contract.synthetic_only !== true ||
    contract.human_approval_required !== true ||
    contract.real_action_executed !== false ||
    contract.operational_state_claimed !== false ||
    contract.physical_safety_determination !== 'not_determined'
  ) {
    return {
      humanApproval: 'NOT VERIFIED',
      realAction: 'NOT VERIFIED',
      operationalState: 'NOT VERIFIED',
      physicalSafety: 'NOT DETERMINED',
    }
  }

  return {
    humanApproval: 'TRUE',
    realAction: 'FALSE',
    operationalState: 'FALSE',
    physicalSafety: 'NOT DETERMINED',
  }
}
