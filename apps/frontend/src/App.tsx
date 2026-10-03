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

const DEMO_REQUEST = {
  schema_version: '1.0' as const,
  use_case: 'ransomware_resilience' as const,
  industry: 'energy',
  site_id: 'synthetic-site-001',
  site_type: 'control_centre',
  scenario_id: 'rw-attack-070891bdbaec',
  observable_input: {
    login_failures: 3,
  },
}

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
  if (typeof value !== 'number') return 'â€”'
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
      const nextResult = await inferRansomware(DEMO_REQUEST)
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
          kicker="RW-120-3 Â· OVERVIEW"
          title="Ransomware resilience posture"
          description="Review scored synthetic evidence, provenance, uncertainty, and human-review recommendations from the backend orchestrator."
        />

        <div className="metric-grid">
          <article className="metric-card">
            <span className="metric-label">Decision</span>
            <strong className={`decision ${statusTone}`}>
              {decisionLabel(result?.decision)}
            </strong>
            <small>Model decision Â· not recomputed by frontend</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Calibrated probability</span>
            <strong>{formatPercent(calibrated)}</strong>
            <small>Calibrated model output</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Runtime</span>
            <strong>{result?.runtime_state?.replace('_', ' ') ?? 'â€”'}</strong>
            <small>Artifact: {result?.artifact_status ?? 'â€”'}</small>
          </article>

          <article className="metric-card">
            <span className="metric-label">Provenance</span>
            <strong>{result?.data_provenance ?? 'â€”'}</strong>
            <small>
              {result?.trace_id ? `Trace: ${result.trace_id.slice(0, 12)}â€¦` : 'No trace loaded'}
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
                <strong>{result?.scenario_id ?? DEMO_REQUEST.scenario_id}</strong>
              </div>
              <div>
                <span>Industry</span>
                <strong>{result?.industry ?? DEMO_REQUEST.industry}</strong>
              </div>
              <div>
                <span>Site</span>
                <strong>{result?.site_id ?? DEMO_REQUEST.site_id}</strong>
              </div>
              <div>
                <span>Site type</span>
                <strong>{result?.site_type ?? DEMO_REQUEST.site_type}</strong>
              </div>
              <div>
                <span>Bundle</span>
                <strong>{result?.model_result?.bundle_version ?? 'â€”'}</strong>
              </div>
              <div>
                <span>Calibration</span>
                <strong>{result?.model_result?.calibration.method ?? 'â€”'}</strong>
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
                      <strong>{item.action ?? 'Review recommendation'}</strong>
                      <p>
                        {item.rationale ??
                          'Evidence is available for human review; no operational action is executed.'}
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
                incident stage Â· severity Â· resilience score Â· asset context Â· recovery context
              </div>
            </div>
          </article>
        </div>
      </>
    )
  }

  function renderScenarioLab() {
    return (
      <>
        <SectionHeader
          kicker="RW-120-4 Â· SCENARIO LAB"
          title="Synthetic scenario"
          description="The dashboard submits a permitted synthetic scenario to the backend orchestrator. The browser never calls the ML service directly."
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

            <div className="detail-grid">
              <div><span>Use case</span><strong>{DEMO_REQUEST.use_case}</strong></div>
              <div><span>Industry</span><strong>{DEMO_REQUEST.industry}</strong></div>
              <div><span>Site</span><strong>{DEMO_REQUEST.site_id}</strong></div>
              <div><span>Site type</span><strong>{DEMO_REQUEST.site_type}</strong></div>
              <div><span>Scenario ID</span><strong>{DEMO_REQUEST.scenario_id}</strong></div>
              <div><span>Observable</span><strong>login_failures = 3</strong></div>
            </div>

            <button className="primary-button scenario-button" type="button" onClick={runAnalysis} disabled={loading}>
              {loading ? 'Running analysisâ€¦' : 'Run synthetic scenario'}
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
          kicker="RW-120-5 Â· DETECTION"
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
          kicker="RW-120-6 Â· TIMELINE"
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
          kicker="RW-120-7 Â· SPREAD"
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
          kicker="RW-120-8 Â· RECOVERY"
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
          kicker="RW-120-9 Â· APPROVAL"
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
          kicker="RW-121-0 Â· EVIDENCE & AUDIT"
          title="Evidence, provenance & audit"
          description="Traceability fields come directly from the backend orchestration response."
        />

        <article className="panel audit-panel">
          <div className="audit-grid">
            <div>
              <span>Request ID</span>
              <code>{result?.request_id ?? 'â€”'}</code>
            </div>
            <div>
              <span>Trace ID</span>
              <code>{result?.trace_id ?? 'â€”'}</code>
            </div>
            <div>
              <span>Task</span>
              <code>{result?.task_id ?? 'â€”'}</code>
            </div>
            <div>
              <span>Data provenance</span>
              <code>{result?.data_provenance ?? 'â€”'}</code>
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
              <div><span>Artifact</span><strong>{result?.artifact_status ?? 'â€”'}</strong></div>
              <div><span>Review state</span><strong>{result?.recommendation_review_state ?? 'â€”'}</strong></div>
              <div><span>Audit latency</span><strong>{result?.audit?.latency_ms != null ? `${result.audit.latency_ms.toFixed(2)} ms` : 'â€”'}</strong></div>
              <div><span>Artifact version</span><strong>{result?.audit?.artifact_versions?.join(', ') ?? 'â€”'}</strong></div>
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
              <div><span>Synthetic only</span><strong>{result?.model_result?.runtime_contract.synthetic_only ? 'TRUE' : 'â€”'}</strong></div>
              <div><span>Human approval</span><strong>{result?.model_result?.runtime_contract.human_approval_required ? 'TRUE' : 'â€”'}</strong></div>
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
          <div className="eyebrow">URAI Â· ENERGY & PETROCHEMICAL</div>
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
                  {loading ? 'Running analysisâ€¦' : 'Run synthetic analysis'}
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
