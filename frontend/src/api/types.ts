// Shared API types for the AI Governance & Compliance Platform.

export type RequirementStatus =
  | "PASS"
  | "PARTIAL"
  | "FAIL"
  | "CANNOT_DETERMINE";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AssessmentStatus =
  | "PENDING"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type ScoreLevel = "REQUIREMENT" | "CONTROL" | "FRAMEWORK" | "OVERALL";

// --- Response envelope ---------------------------------------------------

export interface Pagination {
  count: number;
  page: number;
  pages: number;
  page_size: number;
  next: string | null;
  previous: string | null;
}

export interface Meta {
  pagination?: Pagination;
  count?: number;
  [key: string]: unknown;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
  meta?: Meta;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

// --- Domain types --------------------------------------------------------

export interface Health {
  status: string;
  version: string;
  phase: string;
  time: string;
}

export interface DashboardKpis {
  compliance_score: number | null;
  audit_turnaround_seconds: number | null;
  human_override_rate: number;
  cannot_determine_rate: number;
  framework_coverage: number;
  pending_recommendations: number;
}

export interface DashboardTotals {
  documents: number;
  frameworks: number;
  assessments: number;
  completed_assessments: number;
  requirements_evaluated: number;
  audit_events: number;
}

export interface Dashboard {
  kpis: DashboardKpis;
  totals: DashboardTotals;
  risk_distribution: Record<RiskLevel, number>;
  assessment_status_distribution: Record<AssessmentStatus, number>;
  requirement_status_distribution: Record<RequirementStatus, number>;
  framework_coverage_detail: { total: number; covered: number };
}

export interface Document {
  id: string;
  original_filename: string;
  extension: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  doc_type: string;
  doc_type_display: string;
  status: string;
  status_display: string;
  page_count: number;
  is_scanned: boolean;
  file_url: string;
  created_at: string;
}

export interface Framework {
  id: string;
  name: string;
  version: string;
  publisher: string;
  category: string;
  description: string;
  is_active: boolean;
  requirement_count: number;
  control_count: number;
  config_hash: string;
  synced_at: string;
}

export interface Requirement {
  id: string;
  identifier: string;
  title: string;
  description: string;
  control: string;
  weight: number;
  category: string;
  risk_domain: string;
  control_group: string;
  control_group_title: string;
  evidence_expectations: string[];
  pass_criteria: string;
  partial_criteria: string;
  fail_criteria: string;
  references: string[];
  order: number;
}

export interface FrameworkControl {
  id: string;
  title: string;
  requirements: Requirement[];
}

export interface FrameworkDetail extends Framework {
  scoring_config: Record<string, unknown>;
  controls: FrameworkControl[];
}

export interface Assessment {
  id: string;
  name: string;
  framework: string;
  framework_name: string;
  status: AssessmentStatus;
  overall_score: string | null;
  overall_status: string;
  risk_score: string | null;
  risk_level: RiskLevel | string;
  document_count: number;
  summary: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ScoreBreakdown {
  needs_review?: boolean;
  [key: string]: unknown;
}

export interface Score {
  id: string;
  level: ScoreLevel;
  requirement: string | null;
  requirement_identifier: string;
  control_id: string;
  label: string;
  status: RequirementStatus | string;
  status_display: string;
  confidence: number;
  weight: number;
  normalized_score: string | null;
  reasoning: string;
  missing_information: string[];
  breakdown: ScoreBreakdown;
  is_human_overridden: boolean;
}

export interface Evidence {
  id: string;
  requirement_identifier: string;
  quote: string;
  page: number | null;
  verified: boolean;
  confidence: number;
}

export interface Recommendation {
  id: string;
  requirement_identifier: string;
  title: string;
  description: string;
  rationale: string;
  remediation_steps: string[];
  priority: string;
  priority_display: string;
  priority_rank: number;
  category: string;
  status: string;
  traceability: unknown;
}

export interface AssessmentDetail extends Assessment {
  config_snapshot: Record<string, unknown>;
  error_message: string | null;
  documents: Document[];
  scores: Score[];
  evidence: Evidence[];
  recommendations: Recommendation[];
}

export interface Report {
  id: string;
  assessment: string;
  report_format: "PDF" | "JSON" | string;
  status: string;
  file_url: string;
  download_url: string;
  checksum: string;
  generated_at: string | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  actor_label: string;
  action: string;
  action_display: string;
  entity_type: string;
  entity_id: string;
  summary: string;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  role: string;
  role_display: string;
  organization: string;
}

export interface AuthMe {
  authenticated: boolean;
  user: AuthUser | null;
}
