import type {
  RansomwareInferenceRequest,
  RansomwareApiResult,
  RansomwareResult,
  RansomwareUnavailableResult,
} from '../types/ransomware'

const API_BASE_URL =
  import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000'

const INFER_URL = `${API_BASE_URL}/api/v1/ransomware/infer`

export class RansomwareApiError extends Error {
  readonly kind:
    | 'timeout'
    | 'network'
    | 'http'
    | 'invalid_response'
    | 'unavailable'

  constructor(
    message: string,
    kind:
      | 'timeout'
      | 'network'
      | 'http'
      | 'invalid_response'
      | 'unavailable',
  ) {
    super(message)
    this.name = 'RansomwareApiError'
    this.kind = kind
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isRansomwareResult(value: unknown): value is RansomwareResult {
  if (!isRecord(value)) return false

  const model = value.model_result
  if (!isRecord(model)) return false

  const probabilities = model.probabilities
  if (!isRecord(probabilities)) return false

  const calibrated = probabilities.calibrated

  const validDecision =
    value.decision === 'normal' ||
    value.decision === 'investigate' ||
    value.decision === 'high_risk'

  return (
    typeof value.schema_version === 'string' &&
    typeof value.task_id === 'string' &&
    typeof value.request_id === 'string' &&
    typeof value.trace_id === 'string' &&
    typeof value.scenario_id === 'string' &&
    validDecision &&
    value.runtime_state === 'live_model' &&
    value.artifact_status === 'loaded' &&
    value.data_provenance === 'LIVE_MODEL' &&
    model.decision === value.decision &&
    typeof model.bundle_version === 'string' &&
    typeof model.task === 'string' &&
    typeof model.sector === 'string' &&
    typeof calibrated === 'number' &&
    Number.isFinite(calibrated) &&
    calibrated >= 0 &&
    calibrated <= 1 &&
    isRecord(model.components) &&
    isRecord(model.calibration) &&
    isRecord(model.thresholds) &&
    isRecord(model.runtime_contract) &&
    model.runtime_contract.synthetic_only === true &&
    model.runtime_contract.human_approval_required === true &&
    model.runtime_contract.real_action_executed === false &&
    model.runtime_contract.operational_state_claimed === false &&
    model.runtime_contract.physical_safety_determination === 'not_determined' &&
    Array.isArray(value.recommended_actions) &&
    value.recommended_actions.every((action) => typeof action === 'string') &&
    Array.isArray(value.warnings) &&
    value.warnings.every((warning) => typeof warning === 'string') &&
    value.human_approval_required === true &&
    value.real_action_executed === false &&
    typeof value.canonical_contract_complete === 'boolean'
  )
}

function isUnavailableResult(value: unknown): value is RansomwareUnavailableResult {
  if (!isRecord(value)) return false

  const state = value.runtime_state

  if (
    state !== 'unavailable' &&
    state !== 'degraded' &&
    state !== 'fallback'
  ) return false

  const expectedProvenance =
    state === 'fallback' ? 'FALLBACK' : 'UNAVAILABLE'

  return (
    value.state === state &&
    value.decision === 'unavailable' &&
    value.data_provenance === expectedProvenance &&
    typeof value.request_id === 'string' &&
    typeof value.trace_id === 'string' &&
    Array.isArray(value.warnings) &&
    value.warnings.every((warning) => typeof warning === 'string') &&
    value.fallback_is_live_inference === false &&
    value.human_approval_required === true &&
    value.real_action_executed === false &&
    value.model_result === undefined &&
    value.recommended_actions === undefined &&
    value.artifact_status === undefined &&
    value.canonical_contract_complete === undefined
  )
}

export async function inferRansomware(
  request: RansomwareInferenceRequest,
  timeoutMs = 2500,
): Promise<RansomwareApiResult> {
  const controller = new AbortController()
  const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(INFER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    })

    if (!response.ok) {
      const errorBody = await response.text()
      let detail = ''

      try {
        const parsed = JSON.parse(errorBody) as {
          detail?: unknown
        }
        detail =
          typeof parsed.detail === 'string'
            ? parsed.detail
            : parsed.detail
              ? JSON.stringify(parsed.detail)
              : ''
      } catch {
        detail = errorBody.trim()
      }

      throw new RansomwareApiError(
        `Backend returned HTTP ${response.status}${detail ? `: ${detail}` : '.'}`,
        'http',
      )
    }

    let payload: unknown

    try {
      payload = await response.json()
    } catch {
      throw new RansomwareApiError(
        'Backend returned a non-JSON response.',
        'invalid_response',
      )
    }

    if (!isRansomwareResult(payload) && !isUnavailableResult(payload)) {
      throw new RansomwareApiError(
        'Backend response failed the ransomware result contract.',
        'invalid_response',
      )
    }

    return payload
  } catch (error) {
    if (error instanceof RansomwareApiError) {
      throw error
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new RansomwareApiError(
        `Backend request timed out after ${timeoutMs} ms.`,
        'timeout',
      )
    }

    throw new RansomwareApiError(
      'Backend is unavailable. No fallback is treated as live inference.',
      'network',
    )
  } finally {
    globalThis.clearTimeout(timeout)
  }
}
