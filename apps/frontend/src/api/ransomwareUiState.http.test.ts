import { describe, expect, it } from 'vitest'
import { RansomwareApiError } from './ransomwareApi'
import { getRansomwareUiState } from './ransomwareUiState'

describe('ransomware UI HTTP failure states', () => {
  it('classifies a prohibited synthetic scenario as blocking', () => {
    const error = new RansomwareApiError(
      'Backend returned HTTP 422: synthetic scenario is not permitted: rw-test',
      'http',
    )

    const state = getRansomwareUiState(null, error)

    expect(state.id).toBe('scenario_prohibited')
    expect(state.label).toBe('SCENARIO PROHIBITED')
    expect(state.blocking).toBe(true)
    expect(state.detail).toContain('synthetic scenario is not permitted')
  })

  it('keeps unrelated HTTP failures as backend unavailable', () => {
    const error = new RansomwareApiError(
      'Backend returned HTTP 422: request validation failed.',
      'http',
    )

    const state = getRansomwareUiState(null, error)

    expect(state.id).toBe('backend_unavailable')
    expect(state.blocking).toBe(true)
  })
})
