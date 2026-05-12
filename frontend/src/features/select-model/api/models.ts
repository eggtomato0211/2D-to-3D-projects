import { apiClient } from "@/shared/api/base";

export type ModelSpec = {
  id: string;
  label: string;
  provider: "anthropic" | "openai";
  description: string;
  default: boolean;
};

export type ModelListResponse = {
  models: ModelSpec[];
  default: string;
  active: string;
};

export function listModels(): Promise<ModelListResponse> {
  return apiClient<ModelListResponse>("/models");
}

export function setActiveModel(modelId: string): Promise<{ active: string; requested: string }> {
  return apiClient<{ active: string; requested: string }>("/models/active", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_id: modelId }),
  });
}
