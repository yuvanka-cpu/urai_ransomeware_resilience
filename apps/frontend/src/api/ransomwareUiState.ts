import type {
  ArtifactStatus,
  RansomwareResult,
} from '../types/ransomware'
import { RansomwareApiError } from './ransomwareApi'

export type RansomwareUiStateId =
  | 'ready'
  | 'no_artifact'
  | 'feature_mismatch'
  | 'calibration_stale'
  | 'backend_unavailable'
  | 'ml_timeout'
  | 'partial_sources'
  | 'scenario_prohibited'
  | 'fallback_active'

export interface RansomwareUiState {
  id: RansomwareUiStateId
  label: string
  detail: string
  blocking: boolean
}

const WARNING_PATTERNS: Array<{
  id: RansomwareUiStateId
  pattern: RegExp
  label: string
  blocking: boolean
}> = [
  {
    id: 'calibration_stale',
    pattern: /calibration.*(stale|missing)/i,
    label: 'CALIBRATION STALE / MISSING',
    blocking: true,
  },
  {
    id: 'partial_sources',
    pattern: /(partial|missing).*(source|evidence)/i,
    label: 'PARTIAL SOURCES',
    blocking: false,
  },
  {
    id: 'scenario_prohibited',
    pattern: /(scenario|synthetic mode).*(prohibited|not permitted)/i,
    label: 'SCENARIO PROHIBITED',
    blocking: true,
  },
]

function artifactState(status: ArtifactStatus): RansomwareUiState | null {
  if (status === 'missing') {
    return {
      id: 'no_artifact',
      label: 'NO MODEL ARTIFACT',
      detail: 'Model artifact is missing. Decision must remain unavailable.',
      blocking: true,
    }
  }

  if (status === 'incompatible') {
    return {
      id: 'feature_mismatch',
      label: 'FEATURE / CONTRACT MISMATCH',
      detail: 'Artifact or feature contract is incompatible with the runtime.',
      blocking: true,
    }
  }

  return null
}

export function getRansomwareUiState(
  result: RansomwareResult | null,
  error: RansomwareApiError | null = null,
): RansomwareUiState {
  if (error?.kind === 'timeout') {
    return {
      id: 'ml_timeout',
      label: 'ML TIMEOUT',
      detail: error.message,
      blocking: true,
    }
  }

  if (
    error?.kind === 'http' &&
    /synthetic scenario.*(prohibited|not permitted)/i.test(error.message)
  ) {
    return {
      id: 'scenario_prohibited',
      label: 'SCENARIO PROHIBITED',
      detail: error.message,
      blocking: true,
    }
  }

  if (error) {
    return {
      id: 'backend_unavailable',
      label: 'BACKEND UNAVAILABLE',
      detail: error.message,
      blocking: true,
    }
  }

  if (!result) {
    return {
      id: 'backend_unavailable',
      label: 'BACKEND UNAVAILABLE',
      detail: 'No backend inference result is loaded.',
      blocking: true,
    }
  }

  const artifact = artifactState(result.artifact_status)
  if (artifact) return artifact

  if (
    result.runtime_state === 'fallback' ||
    result.data_provenance === 'FALLBACK'
  ) {
    return {
      id: 'fallback_active',
      label: 'FALLBACK ACTIVE',
      detail: 'Fallback data is active and must not be presented as live-model inference.',
      blocking: true,
    }
  }

  const warning = result.warnings
    .map((item) =>
      WARNING_PATTERNS.find((candidate) => candidate.pattern.test(item)),
    )
    .find(Boolean)

  if (warning) {
    return {
      id: warning.id,
      label: warning.label,
      detail: warning.pattern.source,
      blocking: warning.blocking,
    }
  }

  return {
    id: 'ready',
    label: 'RUNTIME READY',
    detail: 'Backend result passed the frontend envelope checks.',
    blocking: false,
  }
}
