export type Decision =
  | 'normal'
  | 'investigate'
  | 'high_risk'
  | 'unavailable'

export type RuntimeState =
  | 'live_model'
  | 'unavailable'
  | 'degraded'
  | 'fallback'

export type ArtifactStatus =
  | 'loaded'
  | 'missing'
  | 'stale'
  | 'incompatible'
  | 'corrupt'
  | 'unavailable'

export type DataProvenance =
  | 'LIVE_MODEL'
  | 'SYNTHETIC_SCENARIO'
  | 'FALLBACK'
  | 'UNAVAILABLE'

export interface ProbabilityScores {
  catboost?: number
  stacked?: number
  calibrated?: number
}

export interface ComponentScores {
  rule_score?: number
  anomaly_score?: number
  catboost_score?: number
  temporal_score?: number | null
  graph_score?: number
  temporal_missing?: number
}

export interface CalibrationInfo {
  source?: string
  method?: string
}

export interface Thresholds {
  investigate?: number
  high_risk?: number
}

export interface RuntimeContract {
  synthetic_only: boolean
  human_approval_required: boolean
  real_action_executed: false
  operational_state_claimed: false
  physical_safety_determination: 'not_determined'
}

export interface ModelResult {
  bundle_version: string
  task: string
  sector: string
  decision: Decision
  probabilities: ProbabilityScores
  components: ComponentScores
  calibration: CalibrationInfo
  thresholds: Thresholds
  runtime_contract: RuntimeContract
}

export interface AuditEvent {
  request_id?: string
  trace_id?: string
  scenario_id?: string
  artifact_versions?: string[]
  data_provenance?: DataProvenance | string
  warnings?: string[]
  latency_ms?: number | null
  recommendation_review_state?: string
}

export interface RansomwareResult {
  schema_version: string
  task_id: string
  request_id: string
  trace_id: string
  scenario_id: string
  industry: string
  site_id: string
  site_type: string
  runtime_state: RuntimeState
  artifact_status: ArtifactStatus
  data_provenance: DataProvenance
  decision: Decision
  model_result?: ModelResult
  recommendation_review_state?: string
  recommended_actions: string[]
  human_approval_required: true
  real_action_executed: false
  warnings: string[]
  canonical_contract_complete: boolean
  canonical_contract_warning?: string
  audit?: AuditEvent

  // Reserved for the complete canonical contract.
  // These must remain absent/undefined until the backend supplies them.
  incident_stage?: string
  confidence?: number
  severity?: string
  resilience_score?: number
  affected_assets?: string[]
  suspected_assets?: string[]
  critical_services?: string[]
  affected_zones?: string[]
  protected_boundaries?: string[]
  operational_dependency_impact?: string
  propagation_path?: string[]
  evidence_layers?: unknown[]
  timeline?: unknown[]
  backup_readiness?: unknown
  explanations?: string[]
}

export interface RansomwareInferenceRequest {
  schema_version: '1.0'
  use_case: 'ransomware_resilience'
  industry: string
  site_id: string
  site_type: string
  scenario_id: string
  observable_input: Record<string, unknown>
}
