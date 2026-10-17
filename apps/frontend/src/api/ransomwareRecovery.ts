/** RW-120-8: Evidence-gated, read-only recovery availability. */

const API_BASE_URL =
  import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

const RECOVERY_URL =
  `${API_BASE_URL}/api/v1/ransomware/recovery/evidence`

export const RECOVERY_REQUIREMENTS = {
  latest_backup_age: 'Verified backup inventory and timestamp',
  immutable_backup_copy: 'Independent backup immutability evidence',
  last_restore_test: 'Verified restore-test record and outcome',
  configuration_coverage: 'Verified configuration coverage assessment',
  recovery_dependencies: 'Verified recovery dependency assessment',
  resilience_score: 'Approved scoring methodology and verified inputs',
} as const

export type RecoveryRequirement = keyof typeof RECOVERY_REQUIREMENTS

type RecoveryCheck = {
  status: 'unavailable'
  evidence_required: string
  verified_value: null
}

export type RecoveryEvidenceReport = {
  task_id: 'RW-120-8'
  status: 'unavailable'
  analysis_type: 'recovery_evidence_availability'
  data_provenance: 'not_established'
  is_operational_recovery_verified: false
  real_action_executed: false
  human_approval_required: true
  physical_safety_determination: 'not_determined'
  checks: Record<RecoveryRequirement, RecoveryCheck>
  backup_readiness: {
    latest_backup_age_hours: null
    immutable_copy_available: null
    last_restore_test_age_days: null
    configuration_coverage_percent: null
    limitations: string[]
  }
  resilience_score: null
  reason: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function unavailableRecovery(reason: string): RecoveryEvidenceReport {
  const checks = {} as Record<RecoveryRequirement, RecoveryCheck>

  for (const [key, description] of Object.entries(RECOVERY_REQUIREMENTS)) {
    checks[key as RecoveryRequirement] = {
      status: 'unavailable',
      evidence_required: description,
      verified_value: null,
    }
  }

  return {
    task_id: 'RW-120-8',
    status: 'unavailable',
    analysis_type: 'recovery_evidence_availability',
    data_provenance: 'not_established',
    is_operational_recovery_verified: false,
    real_action_executed: false,
    human_approval_required: true,
    physical_safety_determination: 'not_determined',
    checks,
    backup_readiness: {
      latest_backup_age_hours: null,
      immutable_copy_available: null,
      last_restore_test_age_days: null,
      configuration_coverage_percent: null,
      limitations: [reason],
    },
    resilience_score: null,
    reason,
  }
}

export function validateRecoveryEvidence(
  value: unknown,
): RecoveryEvidenceReport {
  const invalid = () =>
    unavailableRecovery('Recovery evidence contract is invalid or incomplete.')

  if (
    !isRecord(value) ||
    value.task_id !== 'RW-120-8' ||
    value.status !== 'unavailable' ||
    value.analysis_type !== 'recovery_evidence_availability' ||
    value.data_provenance !== 'not_established' ||
    value.is_operational_recovery_verified !== false ||
    value.real_action_executed !== false ||
    value.human_approval_required !== true ||
    value.physical_safety_determination !== 'not_determined' ||
    value.resilience_score !== null ||
    typeof value.reason !== 'string' ||
    !value.reason.trim() ||
    !isRecord(value.checks) ||
    !isRecord(value.backup_readiness)
  ) {
    return invalid()
  }

  const expectedKeys = Object.keys(RECOVERY_REQUIREMENTS)
  const actualKeys = Object.keys(value.checks)

  if (
    actualKeys.length !== expectedKeys.length ||
    !expectedKeys.every((key) => actualKeys.includes(key))
  ) {
    return invalid()
  }

  for (const key of expectedKeys) {
    const check = value.checks[key]

    if (
      !isRecord(check) ||
      check.status !== 'unavailable' ||
      check.verified_value !== null ||
      check.evidence_required !==
        RECOVERY_REQUIREMENTS[key as RecoveryRequirement]
    ) {
      return invalid()
    }
  }

  const readiness = value.backup_readiness

  if (
    readiness.latest_backup_age_hours !== null ||
    readiness.immutable_copy_available !== null ||
    readiness.last_restore_test_age_days !== null ||
    readiness.configuration_coverage_percent !== null ||
    !Array.isArray(readiness.limitations) ||
    !readiness.limitations.every(
      (item) => typeof item === 'string' && item.trim().length > 0,
    )
  ) {
    return invalid()
  }

  return value as RecoveryEvidenceReport
}

export async function fetchRecoveryEvidence(
  timeoutMs = 2500,
): Promise<RecoveryEvidenceReport> {
  const controller = new AbortController()
  const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(RECOVERY_URL, {
      method: 'GET',
      signal: controller.signal,
    })

    if (!response.ok) {
      return unavailableRecovery(
        `Recovery backend returned HTTP ${response.status}.`,
      )
    }

    return validateRecoveryEvidence(await response.json())
  } catch {
    return unavailableRecovery('Recovery backend could not be reached.')
  } finally {
    globalThis.clearTimeout(timeout)
  }
}
