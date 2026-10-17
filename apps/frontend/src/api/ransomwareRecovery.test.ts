import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  RECOVERY_REQUIREMENTS,
  fetchRecoveryEvidence,
  unavailableRecovery,
  validateRecoveryEvidence,
} from './ransomwareRecovery'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RW-120-8 recovery evidence safety', () => {
  it('accepts a complete unavailable recovery contract', () => {
    const report = unavailableRecovery('No verified recovery source.')

    const result = validateRecoveryEvidence(report)

    expect(result).toEqual(report)
    expect(result.status).toBe('unavailable')
    expect(result.is_operational_recovery_verified).toBe(false)
  })

  it('reports all six required recovery checks', () => {
    const report = unavailableRecovery('Evidence missing.')

    expect(Object.keys(report.checks)).toEqual(
      Object.keys(RECOVERY_REQUIREMENTS),
    )

    for (const check of Object.values(report.checks)) {
      expect(check.status).toBe('unavailable')
      expect(check.verified_value).toBeNull()
    }
  })

  it('rejects fabricated resilience scores', () => {
    const report = {
      ...unavailableRecovery('Evidence missing.'),
      resilience_score: 95,
    }

    const result = validateRecoveryEvidence(report)

    expect(result.status).toBe('unavailable')
    expect(result.resilience_score).toBeNull()
    expect(result.reason).toContain('invalid')
  })

  it('rejects unsupported operational recovery claims', () => {
    const report = {
      ...unavailableRecovery('Evidence missing.'),
      is_operational_recovery_verified: true,
    }

    const result = validateRecoveryEvidence(report)

    expect(result.is_operational_recovery_verified).toBe(false)
    expect(result.reason).toContain('invalid')
  })

  it('rejects fabricated backup readiness values', () => {
    const original = unavailableRecovery('Evidence missing.')

    const report = {
      ...original,
      backup_readiness: {
        ...original.backup_readiness,
        latest_backup_age_hours: 2,
      },
    }

    const result = validateRecoveryEvidence(report)

    expect(result.backup_readiness.latest_backup_age_hours).toBeNull()
    expect(result.reason).toContain('invalid')
  })

  it('rejects missing recovery requirements', () => {
    const report = structuredClone(
      unavailableRecovery('Evidence missing.'),
    )

    delete (
      report.checks as Partial<typeof report.checks>
    ).recovery_dependencies

    const result = validateRecoveryEvidence(report)

    expect(result.status).toBe('unavailable')
    expect(result.reason).toContain('invalid')
  })

  it('rejects claims that real recovery actions were executed', () => {
    const report = {
      ...unavailableRecovery('Evidence missing.'),
      real_action_executed: true,
    }

    const result = validateRecoveryEvidence(report)

    expect(result.real_action_executed).toBe(false)
    expect(result.reason).toContain('invalid')
  })

  it('fetches and validates backend recovery evidence', async () => {
    const report = unavailableRecovery('No verified recovery source.')

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => report,
    })

    vi.stubGlobal('fetch', mockFetch)

    const result = await fetchRecoveryEvidence()

    expect(result).toEqual(report)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/ransomware/recovery/evidence'),
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('fails closed when the backend returns an error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
      }),
    )

    const result = await fetchRecoveryEvidence()

    expect(result.status).toBe('unavailable')
    expect(result.resilience_score).toBeNull()
    expect(result.reason).toContain('503')
  })

  it('fails closed when the backend is unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('Network unavailable')),
    )

    const result = await fetchRecoveryEvidence()

    expect(result.status).toBe('unavailable')
    expect(result.is_operational_recovery_verified).toBe(false)
    expect(result.real_action_executed).toBe(false)
  })
})
