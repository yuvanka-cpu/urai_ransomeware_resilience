import { useEffect, useMemo, useRef, useState } from 'react'
import {
  fetchRecoveryEvidence,
  unavailableRecovery,
  type RecoveryEvidenceReport,
} from './api/ransomwareRecovery'
import { inferRansomware, RansomwareApiError } from './api/ransomwareApi'
import { getRansomwareUiState } from './api/ransomwareUiState'
import type { RansomwareApiResult, RansomwareResult } from './types/ransomware'
import './App.css'
import { formatAttackRiskScore } from './api/ransomwareRiskScore'
import { getForensicSignals, getForensicInterpretations } from './api/ransomwareForensicEvidence'
import ModelMonitoring from './ModelMonitoring'
import IncidentMetrics from './IncidentMetrics'
import { getApprovalDisplayState } from './api/ransomwareApprovalState'
import {
  fetchObservableTimeline,
  type ObservableTimelineResult,
} from './api/ransomwareTimeline'

type View =
  | 'Overview'
  | 'Scenario Lab'
  | 'Detection'
  | 'Timeline'
  | 'Spread'
  | 'Recovery'
  | 'Approval'
  | 'Evidence & Audit'
  | 'Model Monitoring'
  | 'Incident Metrics'

const SCENARIOS = {
  energy: {
    label: 'Energy · EN-RW-03 · Control centre',
    request: {
      schema_version: '1.0' as const,
      use_case: 'ransomware_resilience' as const,
      industry: 'energy',
      site_id: 'synthetic-energy-001',
      site_type: 'control_centre',
      scenario_id: 'rw-attack-070891bdbaec',
      observable_input: {},
    },
  },
  petrochemical: {
    label: 'Petrochemical · PC-RW-01 · Refinery',
    request: {
      schema_version: '1.0' as const,
      use_case: 'ransomware_resilience' as const,
      industry: 'petrochemical',
      site_id: 'synthetic-petrochemical-001',
      site_type: 'refinery',
      scenario_id: 'rw-attack-69adc08473b6',
      observable_input: {},
    },
  },
  prohibited: {
    label: 'Failure test · Prohibited scenario',
    request: {
      schema_version: '1.0' as const,
      use_case: 'ransomware_resilience' as const,
      industry: 'petrochemical',
      site_id: 'synthetic-petrochemical-001',
      site_type: 'refinery',
      scenario_id: 'rw-attack-902287f49390',
      observable_input: {},
    },
  },
} as const

type ScenarioKey = keyof typeof SCENARIOS

const NAV_ITEMS: View[] = [
  'Overview',
  'Scenario Lab',
  'Detection',
  'Timeline',
  'Spread',
  'Recovery',
  'Approval',
  'Evidence & Audit',
  'Model Monitoring',
  'Incident Metrics',
]

function formatPercent(value?: number) {
  if (typeof value !== 'number') return '-'
  return `${(value * 100).toFixed(1)}%`
}

function decisionLabel(decision?: string) {
  return decision?.replace('_', ' ').toUpperCase() ?? 'UNKNOWN'
}

function scoreWidth(value?: number) {
  if (typeof value !== 'number') return '0%'
  return `${Math.min(Math.max(value * 100, 0), 100)}%`
}

function SectionHeader({
  kicker,
  title,
  description,
}: {
  kicker: string
  title: string
  description?: string
}) {
  return (
    <div className="section-header">
      <div>
        <div className="eyebrow">{kicker}</div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
    </div>
  )
}

function UnavailablePanel({
  title,
  detail,
}: {
  title: string
  detail: string
}) {
  return (
    <article className="panel unavailable-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">EXPLICIT UNAVAILABLE</span>
          <h3>{title}</h3>
        </div>
        <span className="status-dot warning">UNAVAILABLE</span>
      </div>
      <p>{detail}</p>
      <div className="reserved-fields">
        <span>UI rule</span>
        <div>This view does not fabricate missing backend contract data.</div>
      </div>
    </article>
  )
}

function RecoveryView() {
  const [recoveryEvidence, setRecoveryEvidence] =
    useState<RecoveryEvidenceReport>(() =>
      unavailableRecovery('Recovery evidence has not been requested.'),
    )
  const [recoveryLoading, setRecoveryLoading] = useState(true)

  useEffect(() => {
    let active = true

    void fetchRecoveryEvidence().then((report) => {
      if (!active) return
      setRecoveryEvidence(report)
      setRecoveryLoading(false)
    })

    return () => {
      active = false
    }
  }, [])

    const recoveryLabels: Record<keyof typeof recoveryEvidence.checks, string> = {
      latest_backup_age: 'Latest backup age',
      immutable_backup_copy: 'Immutable backup copy',
      last_restore_test: 'Last restore test',
      configuration_coverage: 'Configuration coverage',
      recovery_dependencies: 'Recovery dependencies',
      resilience_score: 'Resilience score',
    }

    return (
      <>
        <SectionHeader
          kicker="RW-120-8 - RECOVERY"
          title="Recovery readiness"
          description="Recovery posture requires independently verified recoverability evidence."
        />

        <UnavailablePanel
          title="Recovery evidence unavailable"
          detail={
            recoveryLoading
              ? 'Checking recovery evidence availability...'
              : recoveryEvidence.reason
          }
        />

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">
                RW-120-8 · RECOVERY EVIDENCE
              </span>
              <h3>Recovery readiness verification</h3>
            </div>
            <span className="status-dot warning">NOT VERIFIED</span>
          </div>

          <div className="detail-grid">
            {Object.entries(recoveryEvidence.checks).map(([key, check]) => (
              <div key={key}>
                <span>
                  {recoveryLabels[key as keyof typeof recoveryLabels]}
                </span>
                <strong>
                  {recoveryLoading
                    ? 'CHECKING'
                    : check.status.toUpperCase()}
                </strong>
                <p className="muted">{check.evidence_required}</p>
              </div>
            ))}
          </div>

          <div className="inline-warning">
            SYNTHETIC DEFENSIVE PROTOTYPE ONLY. NO BACKUP RESTORATION,
            OPERATIONAL RECOVERY, OR PHYSICAL SAFETY OUTCOME IS CLAIMED.
          </div>

          <p className="muted">
            The backend reports evidence availability only. Synthetic ML
            backup and restore features do not establish recoverability.
            No resilience score is calculated without verified evidence
            and an approved scoring methodology.
          </p>
        </article>
      </>
    )
}

function App() {
  const [view, setView] = useState<View>('Overview')
  const analysisRequestId = useRef(0)
  const [scenarioKey, setScenarioKey] = useState<ScenarioKey>('energy')
  const [apiResult, setApiResult] = useState<RansomwareApiResult | null>(null)
  const result: RansomwareResult | null =
    apiResult?.runtime_state === 'live_model' ? apiResult : null
  const [loading, setLoading] = useState(false)
  const [timelineResult, setTimelineResult] =
    useState<ObservableTimelineResult | null>(null)
  const [timelineLoading, setTimelineLoading] = useState(false)
  const [timelineScenarioId, setTimelineScenarioId] = useState<string | null>(null)
  const [error, setError] = useState<RansomwareApiError | null>(null)
  const calibrated = result?.model_result?.probabilities?.calibrated
  const uiState = getRansomwareUiState(apiResult, error)

  const statusTone = useMemo(() => {
    if (!apiResult) return 'neutral'
    if (apiResult.decision === 'unavailable' || apiResult.decision === 'high_risk') {
      return 'danger'
    }
    if (apiResult.decision === 'investigate') return 'warning'
    return 'success'
  }, [apiResult])

  async function runAnalysis() {
    const request = SCENARIOS[scenarioKey].request
    const requestId = ++analysisRequestId.current

    setLoading(true)
    setTimelineLoading(false)
    setTimelineResult(null)
    setTimelineScenarioId(null)
    setError(null)

    try {
      const nextResult = await inferRansomware(request)
      if (requestId !== analysisRequestId.current) return
      setApiResult(nextResult)

      if (
        nextResult.runtime_state === 'live_model' &&
        nextResult.scenario_id === request.scenario_id
      ) {
        setTimelineLoading(true)

        try {
          const timeline = await fetchObservableTimeline(request)
          if (requestId !== analysisRequestId.current) return
          setTimelineResult(timeline)
          setTimelineScenarioId(request.scenario_id)
        } catch {
          // Timeline failure must not invalidate a successful inference.
          if (requestId === analysisRequestId.current) {
            setTimelineResult(null)
            setTimelineScenarioId(null)
          }
        } finally {
          if (requestId === analysisRequestId.current) {
            setTimelineLoading(false)
          }
        }
      }
    } catch (err) {
      if (requestId !== analysisRequestId.current) return
      const apiError =
        err instanceof RansomwareApiError
          ? err
          : new RansomwareApiError('Backend request failed.', 'network')
      setError(apiError)
      setApiResult(null)
      setTimelineResult(null)
      setTimelineScenarioId(null)
    } finally {
      if (requestId === analysisRequestId.current) {
        setLoading(false)
      }
    }
  }

  function renderOverview() {
    return (
      <>
        <SectionHeader
          kicker="RW-120-3 - OVERVIEW"
          title="Ransomware resilience posture"
          description="Review scored synthetic evidence, provenance, uncertainty, and human-review recommendations from the backend orchestrator."
        />

        <div className="metric-grid">
          <article className="metric-card">
            <span className="metric-label">Decision</span>
            <strong className={`decision ${statusTone}`}>
              {decisionLabel(apiResult?.decision)}
            </strong>
            <small>Model decision - not recomputed by frontend</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Calibrated probability</span>
            <strong>{formatPercent(calibrated)}</strong>
            <small>Calibrated model output</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Attack Risk Score</span>
            <strong>
              {formatAttackRiskScore(calibrated)}
            </strong>
            <small>Probability-based indicator; not operational impact</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Model Confidence</span>
            <strong>Not established</strong>
            <small>Independent prediction confidence not yet validated</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Runtime</span>
            <strong>{apiResult?.runtime_state?.replace('_', ' ') ?? '-'}</strong>
            <small>Artifact: {result?.artifact_status ?? '-'}</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Provenance</span>
            <strong>{apiResult?.data_provenance ?? '-'}</strong>
            <small>
              {apiResult?.trace_id ? `Trace: ${apiResult.trace_id.slice(0, 12)}...` : 'No trace loaded'}
            </small>
          </article>
        </div>

        <div className="content-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">MODEL EVIDENCE</span>
                <h3>Component scores</h3>
              </div>
              {result?.runtime_state === "live_model" && <span className="status-dot live">MODEL</span>}
            </div>

            <div className="score-list">
              {[
                ['CatBoost', result?.model_result?.components.catboost_score],
                ['Rule', result?.model_result?.components.rule_score],
                ['Anomaly', result?.model_result?.components.anomaly_score],
                ['Graph', result?.model_result?.components.graph_score],
                ['Temporal', result?.model_result?.components.temporal_score],
              ].map(([label, value]) => (
                <div className="score-row" key={label}>
                  <span>{label}</span>
                  <div className="score-track">
                    <div className="score-fill" style={{ width: scoreWidth(value as number | undefined) }} />
                  </div>
                  <strong>{formatPercent(value as number | undefined)}</strong>
                </div>
              ))}
            </div>

            {result?.model_result?.components.temporal_missing === 1 && (
              <div className="inline-warning">
                Temporal challenger unavailable; calibrated result excludes it.
              </div>
            )}
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">SCENARIO</span>
                <h3>Active context</h3>
              </div>
            </div>

            <div className="detail-grid">
              <div>
                <span>Scenario</span>
                <strong>{result?.scenario_id ?? SCENARIOS[scenarioKey].request.scenario_id}</strong>
              </div>
              <div>
                <span>Industry</span>
                <strong>{result?.industry ?? SCENARIOS[scenarioKey].request.industry}</strong>
              </div>
              <div>
                <span>Site</span>
                <strong>{result?.site_id ?? SCENARIOS[scenarioKey].request.site_id}</strong>
              </div>
              <div>
                <span>Site type</span>
                <strong>{result?.site_type ?? SCENARIOS[scenarioKey].request.site_type}</strong>
              </div>
              <div>
                <span>Bundle</span>
                <strong>{result?.model_result?.bundle_version ?? '-'}</strong>
              </div>
              <div>
                <span>Calibration</span>
                <strong>{result?.model_result?.calibration.method ?? '-'}</strong>
              </div>
            </div>
          </article>
        </div>

        <div className="content-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">AI PLAYBOOK · ADVISORY ONLY</span>
                <h3>Evidence-aware investigation guidance</h3>
              </div>
              <span className="review-chip">
                {result?.recommendation_review_state ?? 'NOT LOADED'}
              </span>
            </div>

            {result?.recommended_actions?.length ? (
              <div className="recommendation-list">
                {result.recommended_actions.map((item, index) => (
                  <div className="recommendation" key={index}>
                    <span className="recommendation-number">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    <div>
                      <strong>{item}</strong>
                      <p>
                        Advisory guidance only. Verify supporting evidence before drawing conclusions; no operational action is executed.
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted">
                {!apiResult
                  ? 'Run the synthetic analysis to load recommendations.'
                  : !result
                    ? 'Recommendations unavailable: live-model inference did not complete.'
                    : 'No recommendations were supplied by the backend.'}
              </p>
            )}

            <div className="safety-strip">
              <span>HUMAN APPROVAL REQUIRED</span>
              <span>REAL ACTION EXECUTED: FALSE</span>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">CONTRACT HEALTH</span>
                <h3>Canonical evidence boundary</h3>
              </div>
              <span className="status-dot warning">
                {!apiResult
                  ? 'NOT LOADED'
                  : !result
                    ? 'UNAVAILABLE'
                    : result.canonical_contract_complete
                      ? 'COMPLETE'
                      : 'PARTIAL'}
              </span>
            </div>

            <div className="contract-state">
              <strong>
                {!apiResult
                  ? 'No inference result loaded'
                  : !result
                    ? 'Canonical evidence unavailable: no live-model result'
                    : result.canonical_contract_complete
                      ? 'Canonical contract complete'
                      : 'Canonical contract incomplete'}
              </strong>
              <p>
                {!apiResult
                  ? 'Run a permitted synthetic scenario to request backend evidence.'
                  : !result
                    ? apiResult.warnings[0] ?? 'Live-model evidence is unavailable.'
                    : result.canonical_contract_warning ??
                      'RW-1006 currently does not supply the complete browser-facing canonical contract.'}
              </p>
            </div>

            <div className="reserved-fields">
              <span>Reserved until backend supplies</span>
              <div>
                incident stage - severity - resilience score - asset context - recovery context
              </div>
            </div>
          </article>
        </div>
      </>
    )
  }

  function renderScenarioLab() {
    const scenario = SCENARIOS[scenarioKey]

    return (
      <>
        <SectionHeader
          kicker="RW-120-4 - SCENARIO LAB"
          title="Synthetic scenario"
          description="The dashboard submits a permitted frozen synthetic scenario to the backend orchestrator. The browser never calls the ML service directly."
        />

        <div className="content-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">REQUEST</span>
                <h3>Scenario inputs</h3>
              </div>
              <span className="boundary-chip">BACKEND ONLY</span>
            </div>

            <div className="scenario-selector">
              <label htmlFor="scenario-select">Walkthrough scenario</label>
              <select
                id="scenario-select"
                value={scenarioKey}
                onChange={(event) => {
                  const nextKey = event.target.value as ScenarioKey
                  ++analysisRequestId.current
                  setScenarioKey(nextKey)
                  setApiResult(null)
                  setTimelineResult(null)
                  setTimelineScenarioId(null)
                  setError(null)
                }}
                disabled={loading}
              >
                {Object.entries(SCENARIOS).map(([key, item]) => (
                  <option key={key} value={key}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="detail-grid">
              <div><span>Use case</span><strong>{scenario.request.use_case}</strong></div>
              <div><span>Industry</span><strong>{scenario.request.industry}</strong></div>
              <div><span>Site</span><strong>{scenario.request.site_id}</strong></div>
              <div><span>Site type</span><strong>{scenario.request.site_type}</strong></div>
              <div><span>Scenario ID</span><strong>{scenario.request.scenario_id}</strong></div>
              <div><span>Observable</span><strong>Frozen scenario event stream</strong></div>
            </div>

            <button
              className="primary-button scenario-button"
              type="button"
              onClick={runAnalysis}
              disabled={loading}
            >
              {loading ? 'Running analysis...' : 'Run synthetic scenario'}
            </button>
          </article>

          <UnavailablePanel
            title="Operational scenario controls"
            detail="The current backend contract does not expose plant/control execution controls, and this frontend does not create them."
          />
        </div>
      </>
    )
  }

  function renderDetection() {
    return (
      <>
        <SectionHeader
          kicker="RW-120-5 - DETECTION"
          title="Detection evidence"
          description="Model outputs are presented as scored evidence. The frontend does not recompute the backend decision."
        />

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">DETECTION RESULT</span>
              <h3>{decisionLabel(apiResult?.decision)}</h3>
            </div>
            <span className={`decision ${statusTone}`}>
              {formatPercent(result?.model_result?.probabilities?.calibrated)}
            </span>
          </div>

          <div className="score-list">
            {[
              ['Calibrated', result?.model_result?.probabilities?.calibrated],
              ['Stacked', result?.model_result?.probabilities?.stacked],
              ['CatBoost', result?.model_result?.probabilities?.catboost],
              ['Rule', result?.model_result?.components.rule_score],
              ['Anomaly', result?.model_result?.components.anomaly_score],
              ['Graph', result?.model_result?.components.graph_score],
            ].map(([label, value]) => (
              <div className="score-row" key={label}>
                <span>{label}</span>
                <div className="score-track">
                  <div className="score-fill" style={{ width: scoreWidth(value as number | undefined) }} />
                </div>
                <strong>{formatPercent(value as number | undefined)}</strong>
              </div>
            ))}
          </div>

          <div className="reserved-fields">
            <span>Decision authority</span>
            <div>The backend/model contract owns the decision; this UI only displays it.</div>
          </div>
        </article>
      </>
    )
  }

  function renderTimeline() {
    const selectedScenarioId = SCENARIOS[scenarioKey].request.scenario_id

    const evidence =
      result?.scenario_id === selectedScenarioId &&
      timelineScenarioId === selectedScenarioId &&
      timelineResult?.scenario_id === selectedScenarioId
        ? timelineResult
        : null

    return (
      <>
        <SectionHeader
          kicker="RW-120-6 - TIMELINE"
          title="Synthetic observable-event timeline"
          description="Chronological synthetic observations supplied and validated by the backend. These are not confirmed ransomware stages or operational incidents."
        />

        {timelineLoading ? (
          <article className="panel">
            <h3>Loading timeline evidence...</h3>
            <p>Waiting for independently validated synthetic observations.</p>
          </article>
        ) : evidence?.status === 'available' ? (
          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">SYNTHETIC DEVELOPMENT EVIDENCE</span>
                <h3>{evidence.event_count} observable events</h3>
              </div>
              <span className="boundary-chip">NOT OPERATIONAL</span>
            </div>

            <p>
              These events are synthetic observations only. Event names and
              attributes do not establish compromise, incident progression,
              physical safety impact, or verified asset propagation.
            </p>

            <div className="detail-grid">
              <div>
                <span>First observation</span>
                <strong>{evidence.first_event_at}</strong>
              </div>
              <div>
                <span>Last observation</span>
                <strong>{evidence.last_event_at}</strong>
              </div>
              <div>
                <span>Observed assets</span>
                <strong>{evidence.observed_asset_ids.length}</strong>
              </div>
              <div>
                <span>Evidence provenance</span>
                <strong>{evidence.data_provenance}</strong>
              </div>
            </div>

            <div className="reserved-fields">
              <span>Sequence fingerprint (SHA-256)</span>
              <div><code>{evidence.sequence_fingerprint_sha256}</code></div>
            </div>

            <div className="reserved-fields">
              <span>Evidence limitations</span>
              <div>{evidence.limitations}</div>
            </div>

            <div className="timeline-events">
              {evidence.timeline.map((event) => (
                <article
                  className="panel"
                  key={`${event.sequence_index}-${event.asset_id}`}
                >
                  <div className="panel-header">
                    <div>
                      <span className="panel-kicker">
                        OBSERVATION {event.sequence_index + 1}
                      </span>
                      <h3>{event.event_type.replaceAll('_', ' ')}</h3>
                    </div>
                    <span className="boundary-chip">SYNTHETIC</span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>Timestamp (UTC/offset)</span>
                      <strong>{event.event_time}</strong>
                    </div>
                    <div>
                      <span>Event family</span>
                      <strong>{event.event_family}</strong>
                    </div>
                    <div>
                      <span>Observed asset ID</span>
                      <strong>{event.asset_id}</strong>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </article>
        ) : (
          <UnavailablePanel
            title="Timeline evidence unavailable"
            detail={
              evidence?.status === 'unavailable'
                ? evidence.reason
                : 'Run a permitted synthetic scenario to request validated observable-event evidence. No canonical incident timeline is inferred.'
            }
          />
        )}
      </>
    )
  }

  function renderSpread() {
    const selectedScenario = SCENARIOS[scenarioKey].request

    const evidence =
      result?.scenario_id === selectedScenario.scenario_id &&
      timelineScenarioId === selectedScenario.scenario_id &&
      timelineResult?.scenario_id === selectedScenario.scenario_id &&
      timelineResult.status === 'available'
        ? timelineResult
        : null

    const sectorNamingMismatch =
      evidence?.observed_asset_ids.some((assetId) => {
        const normalized = assetId.toLowerCase()
        return (
          (selectedScenario.industry === 'petrochemical' &&
            normalized.startsWith('energy-')) ||
          (selectedScenario.industry === 'energy' &&
            normalized.startsWith('petrochemical-'))
        )
      }) ?? false

    return (
      <>
        <SectionHeader
          kicker="RW-120-7 - SPREAD"
          title="Propagation & spread"
          description="Observed synthetic asset context is distinct from verified compromise, propagation, and operational blast radius."
        />

        {timelineLoading ? (
          <article className="panel">
            <h3>Loading asset observations...</h3>
            <p>Waiting for validated synthetic Timeline evidence.</p>
          </article>
        ) : evidence ? (
          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">SYNTHETIC OBSERVABLE EVIDENCE</span>
                <h3>{evidence.observed_asset_ids.length} observed asset identifier(s)</h3>
              </div>
              <span className="boundary-chip">NOT VERIFIED SPREAD</span>
            </div>

            <p>
              These identifiers occur in validated synthetic event records.
              Observation does not establish that an asset is compromised,
              affected, or part of a ransomware propagation path.
            </p>

            <div className="detail-grid">
              <div>
                <span>Scenario industry</span>
                <strong>{selectedScenario.industry}</strong>
              </div>
              <div>
                <span>Synthetic event count</span>
                <strong>{evidence.event_count}</strong>
              </div>
              <div>
                <span>Evidence provenance</span>
                <strong>{evidence.data_provenance}</strong>
              </div>
            </div>

            <div className="reserved-fields">
              <span>Observed asset identifiers</span>
              {evidence.observed_asset_ids.map((assetId) => (
                <div key={assetId}><code>{assetId}</code></div>
              ))}
            </div>

            {sectorNamingMismatch && (
              <div className="inline-warning">
                SYNTHETIC DATA QUALITY WARNING: An observed asset identifier
                uses a sector prefix inconsistent with the selected scenario.
                The original identifier is preserved; its sector association
                has not been independently verified.
              </div>
            )}

            <div className="reserved-fields">
              <span>Evidence limitations</span>
              <div>{evidence.limitations}</div>
            </div>
          </article>
        ) : (
          <UnavailablePanel
            title="Observed asset context unavailable"
            detail="No validated synthetic observable-event evidence is loaded for the selected scenario."
          />
        )}

        <UnavailablePanel
          title="Propagation context unavailable"
          detail="No independently verified affected/suspected asset classification, zone-to-zone propagation path, or operational blast radius is available. Event names such as lateral_movement_observable do not establish confirmed movement."
        />
      </>
    )
  }

  function renderApproval() {
    const approval = getApprovalDisplayState(result)

    return (
      <>
        <SectionHeader
          kicker="RW-120-9 - APPROVAL"
          title="Human approval boundary"
          description="Recommendations are non-executing. Approval remains a human-controlled review state."
        />

        <div className="content-grid">
          <article className="panel approval-panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">SAFETY INVARIANTS</span>
                <h3>Execution boundary</h3>
              </div>
              <span className="status-dot live">ENFORCED</span>
            </div>

            <div className="approval-grid">
              <div><span>Human approval required</span><strong>{approval.humanApproval}</strong></div>
              <div><span>Real action executed</span><strong>{approval.realAction}</strong></div>
              <div><span>Operational state claimed</span><strong>{approval.operationalState}</strong></div>
              <div><span>Physical safety determination</span><strong>{approval.physicalSafety}</strong></div>
            </div>
          </article>

          <UnavailablePanel
            title="Action execution"
            detail="No containment, isolation, account disablement, restore, shutdown, startup, or failover action is exposed by this dashboard."
          />
        </div>
      </>
    )
  }

  function renderAudit() {
    return (
      <>
        <SectionHeader
          kicker="RW-121-0 - EVIDENCE & AUDIT"
          title="Evidence, provenance & audit"
          description="Traceability fields come directly from the backend orchestration response."
        />

        <article className="panel audit-panel">
          <div className="audit-grid">
            <div>
              <span>Request ID</span>
              <code>{result?.request_id ?? '-'}</code>
            </div>
            <div>
              <span>Trace ID</span>
              <code>{result?.trace_id ?? '-'}</code>
            </div>
            <div>
              <span>Task</span>
              <code>{result?.task_id ?? '-'}</code>
            </div>
            <div>
              <span>Data provenance</span>
              <code>{apiResult?.data_provenance ?? '-'}</code>
            </div>
          </div>

          <div className="warnings">
            {(result?.warnings?.length
              ? result.warnings
              : ['No backend result loaded.']).map((warning) => (
              <div className="warning-item" key={warning}>
                <span>!</span>
                {warning}
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">FORENSIC ANALYSIS</span>
              <h3>Preliminary detection evidence review</h3>
            </div>
          </div>

          <div className="detail-grid">
            <div>
              <span>Detection decision</span>
              <strong>{result ? decisionLabel(result.decision) : 'Unavailable'}</strong>
            </div>
            <div>
              <span>Calibrated attack probability</span>
              <strong>{formatAttackRiskScore(result?.model_result?.probabilities?.calibrated)}</strong>
            </div>
            {getForensicSignals(result).map((signal) => (
              <div key={signal.label}>
                <span>{signal.label}</span>
                <strong>{signal.value}</strong>
              </div>
            ))}
            <div>
              <span>Request ID</span>
              <code>{result?.request_id ?? 'Unavailable'}</code>
            </div>
            <div>
              <span>Trace ID</span>
              <code>{result?.trace_id ?? 'Unavailable'}</code>
            </div>
          </div>

          <div className="reserved-fields">
            <span>Evidence interpretation &amp; investigation guidance</span>
            {getForensicInterpretations(result).length > 0 ? (
              getForensicInterpretations(result).map((item) => (
                <div key={item.signal}>
                  <strong>{item.signal}</strong>
                  <p>{item.interpretation}</p>
                  <p><strong>Analyst review:</strong> {item.investigation}</p>
                </div>
              ))
            ) : (
              <div>
                Verified live-model component evidence is unavailable.
                No forensic interpretation is inferred.
              </div>
            )}
          </div>

          <div className="reserved-fields">
            <span>Forensic interpretation limits</span>
            <div>
              These model outputs support preliminary detection review only.
              Component scores are not causal explanations or proof of compromise.
              Affected assets, attacker identity, and propagation path are not
              established by the current live inference response. Human
              investigation is required before drawing operational conclusions.
            </div>
          </div>
        </article>

        <div className="content-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">AUDIT EVENT</span>
                <h3>Gateway traceability</h3>
              </div>
            </div>

            <div className="detail-grid">
              <div><span>Artifact</span><strong>{result?.artifact_status ?? '-'}</strong></div>
              <div><span>Review state</span><strong>{result?.recommendation_review_state ?? '-'}</strong></div>
              <div><span>ML gateway request latency</span><strong>{result?.audit?.latency_ms != null ? `${result.audit.latency_ms.toFixed(2)} ms` : '-'}</strong></div>
              <div><span>Artifact version</span><strong>{result?.audit?.artifact_versions?.join(', ') ?? '-'}</strong></div>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">RUNTIME CONTRACT</span>
                <h3>Safety state</h3>
              </div>
            </div>

            <div className="approval-grid">
              <div><span>Synthetic only</span><strong>{result?.model_result?.runtime_contract.synthetic_only ? 'TRUE' : '-'}</strong></div>
              <div><span>Human approval</span><strong>{result?.model_result?.runtime_contract.human_approval_required ? 'TRUE' : '-'}</strong></div>
              <div><span>Real action</span><strong>FALSE</strong></div>
              <div><span>Physical safety</span><strong>NOT DETERMINED</strong></div>
            </div>
          </article>
        </div>
      </>
    )
  }

  function renderView() {
    if (view === 'Overview') return renderOverview()
    if (view === 'Scenario Lab') return renderScenarioLab()
    if (view === 'Detection') return renderDetection()
    if (view === 'Timeline') return renderTimeline()
    if (view === 'Spread') return renderSpread()
    if (view === 'Recovery') return <RecoveryView />
    if (view === 'Approval') return renderApproval()
    if (view === 'Model Monitoring') return <ModelMonitoring />
    if (view === 'Incident Metrics') return <IncidentMetrics />
    return renderAudit()
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">URAI - ENERGY & PETROCHEMICAL</div>
          <h1>Ransomware Resilience Dashboard</h1>
        </div>

        <div className="topbar-meta">
          <span className="boundary-chip">BACKEND-ONLY API</span>
          <span className="safe-chip">SYNTHETIC DEFENSIVE POC</span>
        </div>
      </header>

      <div className="dashboard">
        <aside className="sidebar">
          <div className="brand-mark">UR</div>

          <nav aria-label="Dashboard sections">
            {NAV_ITEMS.map((item, index) => (
              <button
                key={item}
                className={view === item ? 'nav-item active' : 'nav-item'}
                type="button"
                onClick={() => setView(item)}
              >
                <span>{String(index + 1).padStart(2, '0')}</span>
                {item}
              </button>
            ))}
          </nav>
        </aside>

        <main className="main-content">
          {view === 'Model Monitoring' || view === 'Incident Metrics' ? (
            <section className="state-strip">
              <div>
                <span className="panel-kicker">RW-130 · MONITORING SCOPE</span>
                <strong>OFFLINE SYNTHETIC EVIDENCE</strong>
                <p>
                  Offline monitoring and incident-metric evidence are separate
                  from inference. No live operational metrics are claimed.
                </p>
              </div>
              <span>READ-ONLY</span>
            </section>
          ) : (
            <section className={`state-strip state-${uiState.id}`}>
              <div>
                <span className="panel-kicker">RW-121-1 · RUNTIME STATE</span>
                <strong>{uiState.label}</strong>
                <p>{uiState.detail}</p>
              </div>
              <span>{uiState.blocking ? 'BLOCKING' : 'NON-BLOCKING'}</span>
            </section>
          )}
          {view === 'Overview' || view === 'Scenario Lab' ? null : error && (
            <section className="state-banner danger-banner">
              <div>
                <strong>Backend unavailable</strong>
                <p>{error?.message}</p>
              </div>
              <span>NO LIVE FALLBACK</span>
            </section>
          )}

          {view === 'Overview' && !result && !error && (
            <section className="empty-state">
              <div className="empty-icon">01</div>
              <div>
                <h3>No inference loaded</h3>
                <p>
                  Run the synthetic scenario to populate the dashboard from
                  <code>/api/v1/ransomware/infer</code>.
                </p>
                <button className="primary-button scenario-button" type="button" onClick={runAnalysis} disabled={loading}>
                  {loading ? 'Running analysis...' : 'Run synthetic analysis'}
                </button>
              </div>
            </section>
          )}

          {renderView()}
        </main>
      </div>
    </div>
  )
}

export default App
