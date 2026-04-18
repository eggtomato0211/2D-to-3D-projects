export interface ParameterData {
  name: string;
  value: number;
  parameter_type: string;
  edge_points: number[][];
}

export interface Clarification {
  id: string;
  question: string;
  suggested_answer?: string;
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
