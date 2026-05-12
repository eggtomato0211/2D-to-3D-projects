export interface ParameterData {
  name: string;
  value: number;
  parameter_type: string;
  edge_points: number[][];
}

export type ClarificationAnswer =
  | { kind: "yes" }
  | { kind: "no" }
  | { kind: "custom"; text: string };

export interface Clarification {
  id: string;
  question: string;
  candidates?: ClarificationAnswer[];
}

export type DiscrepancySeverity = "critical" | "major" | "minor";

export interface Discrepancy {
  feature_type: string;
  severity: DiscrepancySeverity;
  description: string;
  expected: string;
  actual: string;
  confidence: "high" | "medium" | "low";
  location_hint?: string | null;
  dimension_hint?: string | null;
}

export interface VerificationResult {
  is_valid: boolean;
  critical_count: number;
  major_count: number;
  minor_count: number;
  discrepancies: Discrepancy[];
}

export interface GenerateResponse {
  model_id: string;
  status: string;
  clarifications?: Clarification[];
  blueprint_id?: string;
  stl_path: string | null;
  error_message: string | null;
  parameters: ParameterData[];
  verification?: VerificationResult | null;
}

export interface ModelStatusResponse {
  model_id: string;
  status: string;
  stl_path: string | null;
  error_message: string | null;
  parameters: ParameterData[];
  verification?: VerificationResult | null;
}
