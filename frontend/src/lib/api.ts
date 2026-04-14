const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface UploadResponse {
  blueprint_id: string;
}

export interface ParameterData {
  name: string;
  value: number;
  parameter_type: string;
  edge_points: number[][];
}

export interface GenerateResponse {
  model_id: string;
  status: string;
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

export async function uploadBlueprint(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/blueprints/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function generateCad(
  blueprintId: string
): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/blueprints/${blueprintId}/generate`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Generation failed: ${res.status}`);
  return res.json();
}

export async function getModelStatus(
  modelId: string
): Promise<ModelStatusResponse> {
  const res = await fetch(`${API_BASE}/models/${modelId}`);
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
  return res.json();
}

export async function updateParameters(
  modelId: string,
  parameters: ParameterData[]
): Promise<ModelStatusResponse> {
  const res = await fetch(`${API_BASE}/models/${modelId}/parameters`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parameters }),
  });
  if (!res.ok) throw new Error(`Parameter update failed: ${res.status}`);
  return res.json();
}

export async function testGenerate(): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/test/generate`, { method: "POST" });
  if (!res.ok) throw new Error(`Test generate failed: ${res.status}`);
  return res.json();
}

export function getStlUrl(stlPath: string): string {
  return `${API_BASE}/files/${stlPath}`;
}
