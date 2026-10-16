export default function IncidentMetrics() {
  const metrics = [
    {
      name: 'Mean Time to Detect (MTTD)',
      definition: 'Incident onset → Detection',
      evidence: 'Verified incident onset and detection timestamps',
    },
    {
      name: 'Mean Response Time',
      definition: 'Detection → Response started',
      evidence: 'Verified detection and response-start timestamps',
    },
    {
      name: 'Mean Recovery Time',
      definition: 'Incident onset → Recovery completed',
      evidence: 'Verified incident onset and recovery-completion timestamps',
    },
  ]

  return (
    <>
      <div className="section-header">
        <div>
          <div className="eyebrow">RW-130-3 · INCIDENT METRICS</div>
          <h2>Incident detection and response timing</h2>
          <p>
            Timing calculations require independently supplied incident
            records. Model windows are not treated as incident timestamps.
          </p>
        </div>
      </div>

      <div className="metric-grid">
        {metrics.map((metric) => (
          <article className="metric-card" key={metric.name}>
            <span className="metric-label">{metric.name}</span>
            <strong>Unavailable</strong>
            <small>{metric.definition}</small>
          </article>
        ))}
      </div>

      <article className="panel unavailable-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">EVIDENCE AVAILABILITY</span>
            <h3>Incident timing measurements unavailable</h3>
          </div>
          <span className="status-dot warning">UNAVAILABLE</span>
        </div>

        <p>
          No independently verified incident timestamp dataset is connected
          to this dashboard. No operational MTTD or response/recovery
          performance is claimed.
        </p>

        <div className="detail-grid">
          {metrics.map((metric) => (
            <div key={metric.name}>
              <span>{metric.name} requires</span>
              <strong>{metric.evidence}</strong>
            </div>
          ))}
        </div>

        <div className="reserved-fields">
          <span>MTTR terminology</span>
          <div>
            MTTR may mean mean time to respond, repair, recover, or resolve.
            The intended definition must be confirmed before reporting MTTR.
            The existing offline calculator separately implements mean
            response time and mean recovery time.
          </div>
        </div>
      </article>
    </>
  )
}
