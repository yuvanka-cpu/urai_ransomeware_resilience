import type { RansomwareInferenceRequest } from '../types/ransomware'

export interface ObservableTimelineEvent {
  sequence_index: number
  event_time: string
  event_family: string
  event_type: string
  asset_id: string
  attributes: Record<string, unknown>
}

export interface ObservableTimelineEvidence {
  schema_version: string
  task_id: 'RW-120-6'
  scenario_id: string
  status: 'available'
  scope: 'offline_synthetic_observable_evidence'
  data_provenance: 'synthetic_development'
  is_operational_incident_timeline: false
  event_count: number
  first_event_at: string
  last_event_at: string
  observed_asset_ids: string[]
  event_family_counts: Record<string, number>
  fingerprint_scope: string
  sequence_fingerprint_sha256: string
  limitations: string
  timeline: ObservableTimelineEvent[]
}

export interface ObservableTimelineUnavailable {
  status: 'unavailable'
  scenario_id: string
  data_provenance: 'synthetic_development'
  is_operational_incident_timeline: false
  timeline: []
  reason: string
}

export type ObservableTimelineResult =
  | ObservableTimelineEvidence
  | ObservableTimelineUnavailable

const FORBIDDEN_KEYS = new Set([
  'ground_truth',
  'ground_truth_label',
  'synthetic_truth',
  'truth_label',
  'is_ransomware',
  'incident_stage_truth',
  'affected_asset_truth',
  'blast_radius_truth',
  'analyst_disposition',
])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function containsTruth(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(containsTruth)
  if (!isRecord(value)) return false

  return Object.entries(value).some(
    ([key, child]) =>
      FORBIDDEN_KEYS.has(key.trim().toLowerCase()) || containsTruth(child),
  )
}

function validAttributes(value: unknown): boolean {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') {
    return true
  }

  if (typeof value === 'number') return Number.isFinite(value)

  if (Array.isArray(value)) return value.every(validAttributes)

  if (isRecord(value)) return Object.values(value).every(validAttributes)

  return false
}

function timestamp(value: unknown): number | null {
  if (typeof value !== 'string') return null

  // Require an explicit UTC offset; local/naive timestamps are not accepted.
  if (!/(Z|[+-]\d{2}:\d{2})$/i.test(value)) return null

  const parsed = Date.parse(value)
  return Number.isFinite(parsed) ? parsed : null
}

function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJson).join(',')}]`
  }

  if (isRecord(value)) {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(',')}}`
  }

  return JSON.stringify(value)
}

async function sha256(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-256', bytes)

  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
}

export function validateTimelineStructure(
  value: unknown,
  expectedScenarioId: string,
): value is ObservableTimelineEvidence {
  if (!isRecord(value) || containsTruth(value)) return false

  if (
    value.schema_version !== '1.0' ||
    value.task_id !== 'RW-120-6' ||
    value.scenario_id !== expectedScenarioId ||
    value.status !== 'available' ||
    value.scope !== 'offline_synthetic_observable_evidence' ||
    value.data_provenance !== 'synthetic_development' ||
    value.is_operational_incident_timeline !== false
  ) return false

  const events = value.timeline
  if (
    !Array.isArray(events) ||
    events.length === 0 ||
    !Number.isSafeInteger(value.event_count) ||
    value.event_count !== events.length
  ) return false

  const assets = new Set<string>()
  const families: Record<string, number> = {}
  let previousTime = -Infinity

  for (let index = 0; index < events.length; index++) {
    const event: unknown = events[index]
    if (!isRecord(event)) return false

    const time = timestamp(event.event_time)

    if (
      event.sequence_index !== index ||
      time === null ||
      time < previousTime ||
      typeof event.event_family !== 'string' ||
      !event.event_family.trim() ||
      typeof event.event_type !== 'string' ||
      !event.event_type.trim() ||
      typeof event.asset_id !== 'string' ||
      !event.asset_id.trim() ||
      !isRecord(event.attributes) ||
      !validAttributes(event.attributes)
    ) return false

    previousTime = time
    assets.add(event.asset_id)
    families[event.event_family] = (families[event.event_family] ?? 0) + 1
  }

  if (
    timestamp(value.first_event_at) === null ||
    timestamp(value.first_event_at) !== timestamp(events[0].event_time) ||
    timestamp(value.last_event_at) !== timestamp(events[events.length - 1].event_time)
  ) return false

  if (
    !Array.isArray(value.observed_asset_ids) ||
    JSON.stringify(value.observed_asset_ids) !==
      JSON.stringify([...assets].sort())
  ) return false

  if (!isRecord(value.event_family_counts)) return false

  const actualFamilies = value.event_family_counts
  const expectedFamilyKeys = Object.keys(families).sort()

  if (
    JSON.stringify(Object.keys(actualFamilies).sort()) !==
      JSON.stringify(expectedFamilyKeys) ||
    expectedFamilyKeys.some((key) => actualFamilies[key] !== families[key])
  ) return false

  return (
    typeof value.sequence_fingerprint_sha256 === 'string' &&
    /^[0-9a-f]{64}$/.test(value.sequence_fingerprint_sha256) &&
    typeof value.fingerprint_scope === 'string' &&
    !!value.fingerprint_scope.trim() &&
    typeof value.limitations === 'string' &&
    !!value.limitations.trim()
  )
}

// The browser must never call the internal ML service directly.
// A separate backend API request function will be added after validation tests.
export type TimelineRequest = RansomwareInferenceRequest


export async function verifyTimelineEvidence(
  value: unknown,
  expectedScenarioId: string,
): Promise<boolean> {
  if (!validateTimelineStructure(value, expectedScenarioId)) return false

  const material = value.timeline.map((event) => ({
    sequence_index: event.sequence_index,
    event_family: event.event_family,
    event_type: event.event_type,
    asset_id: event.asset_id,
    attributes: event.attributes,
  }))

  const calculated = await sha256(canonicalJson(material))
  return calculated === value.sequence_fingerprint_sha256
}

const TIMELINE_API_BASE =
  import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000'

const TIMELINE_URL =
  `${TIMELINE_API_BASE}/api/v1/ransomware/observable-timeline`

export async function fetchObservableTimeline(
  request: TimelineRequest,
  timeoutMs = 5000,
): Promise<ObservableTimelineResult> {
  const controller = new AbortController()
  const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(TIMELINE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`Timeline backend returned HTTP ${response.status}`)
    }

    const payload: unknown = await response.json()

    if (
      isRecord(payload) &&
      payload.status === 'unavailable' &&
      payload.scenario_id === request.scenario_id &&
      payload.data_provenance === 'synthetic_development' &&
      payload.is_operational_incident_timeline === false &&
      Array.isArray(payload.timeline) &&
      payload.timeline.length === 0 &&
      typeof payload.reason === 'string' &&
      payload.reason.trim().length > 0
    ) {
      return payload as unknown as ObservableTimelineUnavailable
    }

    if (await verifyTimelineEvidence(payload, request.scenario_id)) {
      return payload as ObservableTimelineEvidence
    }

    throw new Error('Timeline evidence failed validation.')
  } finally {
    globalThis.clearTimeout(timeout)
  }
}
