import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  inferRansomware,
  RansomwareApiError,
} from './ransomwareApi'

const VALID_REQUEST = {
  schema_version: '1.0' as const,
  use_case: 'ransomware_resilience' as const,
  industry: 'energy',
  site_id: 'synthetic-site-001',
  site_type: 'control_centre',
  scenario_id: 'rw-attack-070891bdbaec',
  observable_input: { login_failures: 3 },
}

const VALID_RESPONSE = {
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
  model_result: {
    bundle_version: 'rw0906_v1',
    task: 'RW-100-3',
    sector: 'energy',
    decision: 'investigate',
    probabilities: {
      catboost: 0.31,
      stacked: 0.3,
      calibrated: 0.29,
    },
    components: {
      rule_score: 0.25,
      anomaly_score: 0.2,
      catboost_score: 0.31,
      temporal_score: null,
      graph_score: 0.18,
      temporal_missing: 1,
    },
    calibration: {
      source: 'synthetic',
      method: 'sigmoid',
    },
    thresholds: {
      investigate: 0.2,
      high_risk: 0.7,
    },
    runtime_contract: {
      synthetic_only: true,
      human_approval_required: true,
      real_action_executed: false,
      operational_state_claimed: false,
      physical_safety_determination: 'not_determined',
    },
  },
  recommendation_review_state: 'pending_review',
  recommended_actions: [],
  human_approval_required: true,
  real_action_executed: false,
  warnings: [],
  canonical_contract_complete: false,
  canonical_contract_warning: 'Incomplete canonical contract.',
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('RW-120-2 ransomware API adapter', () => {
  it('accepts a valid backend result contract', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(VALID_RESPONSE), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    const result = await inferRansomware(VALID_REQUEST)

    if (result.runtime_state !== 'live_model') {
      throw new Error('Expected a live-model inference response.')
    }

    expect(result.task_id).toBe('RW-110-1')
    expect(result.decision).toBe('investigate')
    expect(result.human_approval_required).toBe(true)
    expect(result.real_action_executed).toBe(false)
  })

  it('accepts a genuine backend unavailable response without fabricated model evidence', async () => {
    const unavailableResponse = {
      state: 'unavailable',
      runtime_state: 'unavailable',
      decision: 'unavailable',
      data_provenance: 'UNAVAILABLE',
      request_id: 'req-unavailable-001',
      trace_id: 'trace-unavailable-001',
      warnings: ['ML service dependency unavailable'],
      fallback_is_live_inference: false,
      human_approval_required: true,
      real_action_executed: false,
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(unavailableResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    const result = await inferRansomware(VALID_REQUEST)

    expect(result.decision).toBe('unavailable')
    expect(result.runtime_state).toBe('unavailable')
    expect(result.data_provenance).toBe('UNAVAILABLE')
    expect(result.human_approval_required).toBe(true)
    expect(result.real_action_executed).toBe(false)
    expect('model_result' in result).toBe(false)
    expect('recommended_actions' in result).toBe(false)
    expect('artifact_status' in result).toBe(false)
  })

  it.each([
    ['degraded', 'UNAVAILABLE'],
    ['fallback', 'FALLBACK'],
  ] as const)(
    'accepts a safe %s response with %s provenance',
    async (runtimeState, provenance) => {
      const response = {
        state: runtimeState,
        runtime_state: runtimeState,
        decision: 'unavailable',
        data_provenance: provenance,
        request_id: 'req-failure-001',
        trace_id: 'trace-failure-001',
        warnings: ['Live-model inference unavailable'],
        fallback_is_live_inference: false,
        human_approval_required: true,
        real_action_executed: false,
      }

      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue(
          new Response(JSON.stringify(response), { status: 200 }),
        ),
      )

      const result = await inferRansomware(VALID_REQUEST)

      expect(result.runtime_state).toBe(runtimeState)
      expect(result.data_provenance).toBe(provenance)
      expect(result.decision).toBe('unavailable')
      expect('model_result' in result).toBe(false)
    },
  )

  it.each([
    { human_approval_required: false },
    { real_action_executed: true },
    { fallback_is_live_inference: true },
    { model_result: { decision: 'normal' } },
    { recommended_actions: ['Execute containment'] },
    { artifact_status: 'loaded' },
    { canonical_contract_complete: true },
    { data_provenance: 'LIVE_MODEL' },
  ])('rejects an unsafe unavailable response: %j', async (override) => {
    const response = {
      state: 'unavailable',
      runtime_state: 'unavailable',
      decision: 'unavailable',
      data_provenance: 'UNAVAILABLE',
      request_id: 'req-unsafe-001',
      trace_id: 'trace-unsafe-001',
      warnings: ['ML service unavailable'],
      fallback_is_live_inference: false,
      human_approval_required: true,
      real_action_executed: false,
      ...override,
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(response), { status: 200 }),
      ),
    )

    await expect(inferRansomware(VALID_REQUEST)).rejects.toMatchObject({
      kind: 'invalid_response',
    })
  })

  it.each([
    {
      name: 'fallback runtime with normal decision',
      override: { runtime_state: 'fallback', data_provenance: 'FALLBACK' },
    },
    {
      name: 'fallback provenance on live-model runtime',
      override: { data_provenance: 'FALLBACK' },
    },
    {
      name: 'missing model evidence',
      override: { model_result: undefined },
    },
    {
      name: 'calibrated probability above one',
      override: {
        model_result: {
          ...VALID_RESPONSE.model_result,
          probabilities: {
            ...VALID_RESPONSE.model_result.probabilities,
            calibrated: 1.5,
          },
        },
      },
    },
    {
      name: 'conflicting nested decision',
      override: {
        model_result: {
          ...VALID_RESPONSE.model_result,
          decision: 'normal',
        },
      },
    },
    {
      name: 'unsafe nested runtime contract',
      override: {
        model_result: {
          ...VALID_RESPONSE.model_result,
          runtime_contract: {
            ...VALID_RESPONSE.model_result.runtime_contract,
            real_action_executed: true,
          },
        },
      },
    },
  ])('rejects a misleading live-model response: $name', async ({ override }) => {
    const response = {
      ...VALID_RESPONSE,
      ...override,
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(response), { status: 200 }),
      ),
    )

    await expect(inferRansomware(VALID_REQUEST)).rejects.toMatchObject({
      kind: 'invalid_response',
    })
  })

  it('rejects an invalid backend response contract', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ decision: 'investigate' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(inferRansomware(VALID_REQUEST)).rejects.toMatchObject({
      kind: 'invalid_response',
    })
  })

  it('maps HTTP failures explicitly', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('backend failure', { status: 503 }),
      ),
    )

    await expect(inferRansomware(VALID_REQUEST)).rejects.toMatchObject({
      kind: 'http',
    })
  })

  it('maps network failures without creating a fallback result', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    )

    try {
      await inferRansomware(VALID_REQUEST)
      throw new Error('expected adapter failure')
    } catch (error) {
      expect(error).toBeInstanceOf(RansomwareApiError)
      expect((error as RansomwareApiError).kind).toBe('network')
      expect((error as RansomwareApiError).message).toContain(
        'No fallback is treated as live inference.',
      )
    }
  })

  it('maps request timeout explicitly', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(
        (_input: RequestInfo | URL, init?: RequestInit) =>
          new Promise((_resolve, reject) => {
            init?.signal?.addEventListener('abort', () =>
              reject(new DOMException('Aborted', 'AbortError')),
            )
          }),
      ),
    )

    await expect(inferRansomware(VALID_REQUEST, 1)).rejects.toMatchObject({
      kind: 'timeout',
    })
  })
})
