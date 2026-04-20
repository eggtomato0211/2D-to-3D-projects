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
  suggested_answer?: ClarificationAnswer | null;
}

export interface GenerateResponse {
  model_id: string;
  status: string;
  clarifications?: Clarification[];
  blueprint_id?: string;
  stl_path: string | null;
  error_message: string | null;
  parameters: ParameterData[];
}

export interface ModelStatusResponse {
  model_id: string;
  status: string;
  stl_path: string | null;
  error_message: string | null;
  parameters: ParameterData[];
}
