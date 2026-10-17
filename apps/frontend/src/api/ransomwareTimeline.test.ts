import { describe, expect, it } from 'vitest'
import {
  validateTimelineStructure,
  verifyTimelineEvidence,
} from './ransomwareTimeline'

const SCENARIO_ID = 'rw-attack-070891bdbaec'

function makeEvidence() {
  return {
    schema_version: '1.0',
    task_id: 'RW-120-6',
    scenario_id: SCENARIO_ID,
    status: 'available',
    scope: 'offline_synthetic_observable_evidence',
    data_provenance: 'synthetic_development',
    is_operational_incident_timeline: false,
    event_count: 1,
    first_event_at: '2026-01-01T06:00:00Z',
    last_event_at: '2026-01-01T06:00:00Z',
    observed_asset_ids: ['synthetic-asset-001'],
    event_family_counts: { synthetic: 1 },
    fingerprint_scope: 'observable_event_sequence',
    sequence_fingerprint_sha256: 'a'.repeat(64),
    limitations: 'Synthetic observations only; no verified incident.',
    timeline: [
      {
        sequence_index: 0,
        event_time: '2026-01-01T06:00:00Z',
        event_family: 'synthetic',
        event_type: 'observable_activity',
        asset_id: 'synthetic-asset-001',
        attributes: { observable_only: true },
      },
    ],
  }
}

describe('RW-120-6 frontend timeline validation', () => {
  it('accepts structurally valid synthetic evidence', () => {
    expect(validateTimelineStructure(makeEvidence(), SCENARIO_ID)).toBe(true)
  })

  it('rejects mismatched scenario identity', () => {
    expect(
      validateTimelineStructure(makeEvidence(), 'different-scenario'),
    ).toBe(false)
  })

  it('rejects operational incident claims', () => {
    const evidence = makeEvidence()
    evidence.is_operational_incident_timeline = true
    expect(validateTimelineStructure(evidence, SCENARIO_ID)).toBe(false)
  })

  it('rejects forbidden truth-bearing attributes', () => {
    const evidence = makeEvidence()
    const modified = {
      ...evidence,
      timeline: [
        {
          ...evidence.timeline[0],
          attributes: {
            observable_only: true,
            ground_truth_label: 'ransomware',
          },
        },
      ],
    }

    expect(validateTimelineStructure(modified, SCENARIO_ID)).toBe(false)
  })

  it('rejects a fingerprint that does not match the event content', async () => {
    expect(await verifyTimelineEvidence(makeEvidence(), SCENARIO_ID)).toBe(false)
  })

  it('rejects malformed timestamps', () => {
    const evidence = makeEvidence()
    evidence.timeline[0].event_time = '2026-01-01T06:00:00'

    expect(validateTimelineStructure(evidence, SCENARIO_ID)).toBe(false)
  })

  it('rejects mismatched event counts', () => {
    const evidence = makeEvidence()
    evidence.event_count = 2

    expect(validateTimelineStructure(evidence, SCENARIO_ID)).toBe(false)
  })
})

import energyTimelineFixture from './fixtures/rw1206_energy_timeline.json'

describe('RW-120-6 genuine backend evidence', () => {
  it('verifies the Python-generated SHA-256 fingerprint', async () => {
    expect(
      await verifyTimelineEvidence(energyTimelineFixture, SCENARIO_ID),
    ).toBe(true)
  })

  it('rejects modified event attributes with the original fingerprint', async () => {
    const modified = structuredClone(energyTimelineFixture)

    modified.timeline[0].attributes.observable_only = false

    expect(
      await verifyTimelineEvidence(modified, SCENARIO_ID),
    ).toBe(false)
  })

  it('rejects modified event types with the original fingerprint', async () => {
    const modified = structuredClone(energyTimelineFixture)

    modified.timeline[0].event_type = 'modified_observable'

    expect(
      await verifyTimelineEvidence(modified, SCENARIO_ID),
    ).toBe(false)
  })
})

import { afterEach, vi } from 'vitest'
import { fetchObservableTimeline } from './ransomwareTimeline'

const timelineRequest = {
  schema_version: '1.0' as const,
  use_case: 'ransomware_resilience' as const,
  industry: 'energy',
  site_id: 'synthetic-energy-001',
  site_type: 'control_centre',
  scenario_id: SCENARIO_ID,
  observable_input: {},
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RW-120-6 timeline backend client', () => {
  it('accepts genuine backend evidence', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => structuredClone(energyTimelineFixture),
    }))

    const result = await fetchObservableTimeline(timelineRequest)

    expect(result.status).toBe('available')
    if (result.status === 'available') {
      expect(result.event_count).toBe(24)
      expect(result.is_operational_incident_timeline).toBe(false)
    }
  })

  it('accepts explicit unavailable evidence', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'unavailable',
        scenario_id: SCENARIO_ID,
        data_provenance: 'synthetic_development',
        is_operational_incident_timeline: false,
        timeline: [],
        reason: 'No permitted development-only timeline evidence is available.',
      }),
    }))

    const result = await fetchObservableTimeline(timelineRequest)

    expect(result.status).toBe('unavailable')
  })

  it('rejects evidence belonging to another scenario', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...energyTimelineFixture,
        scenario_id: 'another-scenario',
      }),
    }))

    await expect(fetchObservableTimeline(timelineRequest)).rejects.toThrow(
      'Timeline evidence failed validation.',
    )
  })

  it('rejects tampered event evidence', async () => {
    const modified = structuredClone(energyTimelineFixture)
    modified.timeline[0].event_type = 'tampered_event'

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => modified,
    }))

    await expect(fetchObservableTimeline(timelineRequest)).rejects.toThrow(
      'Timeline evidence failed validation.',
    )
  })

  it('rejects backend HTTP errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
    }))

    await expect(fetchObservableTimeline(timelineRequest)).rejects.toThrow(
      'Timeline backend returned HTTP 503',
    )
  })

  it('rejects network failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(
      new TypeError('Failed to fetch'),
    ))

    await expect(fetchObservableTimeline(timelineRequest)).rejects.toThrow()
  })
})
