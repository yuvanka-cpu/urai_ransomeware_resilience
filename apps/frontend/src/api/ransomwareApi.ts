import type {
  RansomwareInferenceRequest,
  RansomwareResult,
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

  return (
    typeof value.schema_version === 'string' &&
    typeof value.task_id === 'string' &&
    typeof value.request_id === 'string' &&
    typeof value.trace_id === 'string' &&
    typeof value.scenario_id === 'string' &&
    typeof value.decision === 'string' &&
    typeof value.runtime_state === 'string' &&
    typeof value.artifact_status === 'string' &&
    typeof value.data_provenance === 'string' &&
    Array.isArray(value.recommended_actions) &&
    Array.isArray(value.warnings) &&
    value.human_approval_required === true &&
    value.real_action_executed === false &&
    typeof value.canonical_contract_complete === 'boolean'
  )
}

export async function inferRansomware(
  request: RansomwareInferenceRequest,
  timeoutMs = 2500,
): Promise<RansomwareResult> {
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

    if (!isRansomwareResult(payload)) {
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
