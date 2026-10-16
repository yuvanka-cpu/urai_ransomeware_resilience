import { useEffect, useState } from 'react'
import {
  fetchDataDriftReport,
  type DataDriftReport,
} from './api/ransomwareMonitoring'

export default function ModelMonitoring() {
  const [report, setReport] = useState<DataDriftReport | null>(null)

  useEffect(() => {
    let active = true

    fetchDataDriftReport().then((data) => {
      if (active) setReport(data)
    })

    return () => {
      active = false
    }
  }, [])

  const available =
    report?.status === 'drift_detected' ||
    report?.status === 'no_drift_detected'

  const flagged = available
    ? (report.drifted_features ?? [])
    : []

  return (
    <>
      <div className="section-header">
        <div>
          <div className="eyebrow">RW-130 · MODEL MONITORING</div>
          <h2>Model monitoring evidence</h2>
          <p>
            Read-only analysis of synthetic development evidence.
            No production monitoring or operational action is performed.
          </p>
        </div>
      </div>

      <article className="panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">RW-130-1 · DATA DRIFT</span>
            <h3>Feature distribution comparison</h3>
          </div>
          <span className="status-dot warning">
            {report === null
              ? 'LOADING'
              : available
                ? report.status === 'drift_detected'
                  ? 'SHIFT DETECTED'
                  : 'NO SHIFT DETECTED'
                : 'UNAVAILABLE'}
          </span>
        </div>

        <div className="inline-warning">
          OFFLINE SYNTHETIC TRAIN–VALIDATION COMPARISON.
          NOT CHRONOLOGICAL DRIFT OR LIVE PRODUCTION MONITORING.
        </div>

        {available ? (
          <>
            <div className="detail-grid">
              <div>
                <span>Reference dataset</span>
                <strong>Training · {report.reference_count} observations</strong>
              </div>
              <div>
                <span>Comparison dataset</span>
                <strong>Validation · {report.current_count} observations</strong>
              </div>
              <div>
                <span>PSI threshold</span>
                <strong>{report.threshold?.toFixed(2)}</strong>
              </div>
              <div>
                <span>Features evaluated</span>
                <strong>{Object.keys(report.feature_psi ?? {}).length}</strong>
              </div>
              <div>
                <span>Features above threshold</span>
                <strong>{flagged.length}</strong>
              </div>
              <div>
                <span>Evidence provenance</span>
                <strong>synthetic_development</strong>
              </div>
            </div>

            <div className="reserved-fields">
              <span>Flagged feature PSI values</span>
              <div>
                {flagged.length ? (
                  flagged.map((feature) => (
                    <p key={feature}>
                      <code>{feature}</code>
                      {' — PSI '}
                      <strong>{report.feature_psi?.[feature]?.toFixed(4)}</strong>
                    </p>
                  ))
                ) : (
                  <p>No features exceeded the configured PSI threshold.</p>
                )}
              </div>
            </div>

            <p className="muted">
              PSI measures differences between feature distributions.
              A flagged feature does not establish an attack, model failure,
              or deterioration in detection performance.
            </p>
          </>
        ) : (
          <p className="muted">
            {report?.reason ??
              'Loading the offline monitoring evidence from the backend.'}
          </p>
        )}
      </article>

      <article className="panel unavailable-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">RW-130-2 · MODEL DRIFT</span>
            <h3>Detection performance over time</h3>
          </div>
          <span className="status-dot warning">UNAVAILABLE</span>
        </div>

        <p>
          No independently evaluated, compatible chronological performance
          periods are available. The dashboard cannot establish model
          performance drift from the current synthetic development split.
        </p>
      </article>
    </>
  )
}
