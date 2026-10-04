import { useMemo, useState } from 'react'
import { inferRansomware, RansomwareApiError } from './api/ransomwareApi'
import { getRansomwareUiState } from './api/ransomwareUiState'
import type { RansomwareResult } from './types/ransomware'
import './App.css'

type View =
  | 'Overview'
  | 'Scenario Lab'
  | 'Detection'
  | 'Timeline'
  | 'Spread'
  | 'Recovery'
  | 'Approval'
  | 'Evidence & Audit'

const SCENARIOS = {
  energy: {
    label: 'Energy · EN-RW-01 · Control centre',
    request: {
      schema_version: '1.0' as const,
      use_case: 'ransomware_resilience' as const,
      industry: 'energy',
      site_id: 'synthetic-energy-001',
      site_type: 'control_centre',
      scenario_id: 'rw-attack-6ecce30389a5',
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

function App() {
  const [view, setView] = useState<View>('Overview')
  const [scenarioKey, setScenarioKey] = useState<ScenarioKey>('energy')
  const [result, setResult] = useState<RansomwareResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const calibrated = result?.model_result?.probabilities?.calibrated
  const uiState = getRansomwareUiState(
    result,
    error ? new RansomwareApiError(error, 'network') : null,
  )

  const statusTone = useMemo(() => {
    if (!result) return 'success'
    if (result.decision === 'unavailable' || result.decision === 'high_risk') {
      return 'danger'
    }
    if (result.decision === 'investigate') return 'warning'
    return 'success'
  }, [result])

  async function runAnalysis() {
    setLoading(true)
    setError(null)

    try {
      const nextResult = await inferRansomware(SCENARIOS[scenarioKey].request)
      setResult(nextResult)
    } catch (err) {
      const message =
        err instanceof RansomwareApiError ? err.message : 'Backend request failed.'
      setError(message)
      setResult(null)
    } finally {
      setLoading(false)
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
              {decisionLabel(result?.decision)}
            </strong>
            <small>Model decision - not recomputed by frontend</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Calibrated probability</span>
            <strong>{formatPercent(calibrated)}</strong>
            <small>Calibrated model output</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Runtime</span>
            <strong>{result?.runtime_state?.replace('_', ' ') ?? '-'}</strong>
            <small>Artifact: {result?.artifact_status ?? '-'}</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Provenance</span>
            <strong>{result?.data_provenance ?? '-'}</strong>
            <small>
              {result?.trace_id ? `Trace: ${result.trace_id.slice(0, 12)}...` : 'No trace loaded'}
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
              {result && <span className="status-dot live">MODEL</span>}
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
                <span className="panel-kicker">RECOMMENDATIONS</span>
                <h3>Human review queue</h3>
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
                        Evidence is available for human review; no operational action is executed.
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted">Run the synthetic analysis to load recommendations.</p>
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
                {result?.canonical_contract_complete ? 'COMPLETE' : 'PARTIAL'}
              </span>
            </div>

            <div className="contract-state">
              <strong>
                {result?.canonical_contract_complete
                  ? 'Canonical contract complete'
                  : 'Canonical contract incomplete'}
              </strong>
              <p>
                {result?.canonical_contract_warning ??
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
                  setScenarioKey(nextKey)
                  setResult(null)
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
              <h3>{decisionLabel(result?.decision)}</h3>
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
    return (
      <>
        <SectionHeader
          kicker="RW-120-6 - TIMELINE"
          title="Incident timeline"
          description="Timeline visualization is reserved for backend timeline evidence."
        />
        <UnavailablePanel
          title="Timeline data unavailable"
          detail="The current RW-1006 response does not emit the canonical incident timeline. No synthetic timeline is invented by the frontend."
        />
      </>
    )
  }

  function renderSpread() {
    return (
      <>
        <SectionHeader
          kicker="RW-120-7 - SPREAD"
          title="Propagation & spread"
          description="Propagation views require canonical asset, zone, and propagation-path evidence."
        />
        <UnavailablePanel
          title="Propagation context unavailable"
          detail="The current RW-1006 response does not emit full affected/suspected asset context, zones, or a canonical propagation path."
        />
      </>
    )
  }

  function renderRecovery() {
    return (
      <>
        <SectionHeader
          kicker="RW-120-8 - RECOVERY"
          title="Recovery readiness"
          description="Recovery posture will be rendered only from backend-provided recoverability evidence."
        />
        <UnavailablePanel
          title="Recovery evidence unavailable"
          detail="The current backend response does not emit backup readiness, recovery context, or resilience score. The frontend does not infer them."
        />
      </>
    )
  }

  function renderApproval() {
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
              <div><span>Human approval required</span><strong>TRUE</strong></div>
              <div><span>Real action executed</span><strong>FALSE</strong></div>
              <div><span>Operational state claimed</span><strong>FALSE</strong></div>
              <div><span>Physical safety determination</span><strong>NOT DETERMINED</strong></div>
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
              <code>{result?.data_provenance ?? '-'}</code>
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
              <div><span>Audit latency</span><strong>{result?.audit?.latency_ms != null ? `${result.audit.latency_ms.toFixed(2)} ms` : '-'}</strong></div>
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
    if (view === 'Recovery') return renderRecovery()
    if (view === 'Approval') return renderApproval()
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
          <section className={`state-strip state-${uiState.id}`}>
            <div>
              <span className="panel-kicker">RW-121-1 · RUNTIME STATE</span>
              <strong>{uiState.label}</strong>
              <p>{uiState.detail}</p>
            </div>
            <span>{uiState.blocking ? 'BLOCKING' : 'NON-BLOCKING'}</span>
          </section>
          {view === 'Overview' || view === 'Scenario Lab' ? null : error && (
            <section className="state-banner danger-banner">
              <div>
                <strong>Backend unavailable</strong>
                <p>{error}</p>
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
