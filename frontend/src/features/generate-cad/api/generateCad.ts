import { apiClient } from "@/shared/api/base";
import type {
  GenerateResponse,
  ModelStatusResponse,
} from "@/entities/cad-model/model/types";

export function generateCad(
  blueprintId: string,
  vlmModelId: string | null,
): Promise<GenerateResponse> {
  return apiClient<GenerateResponse>(`/blueprints/${blueprintId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: vlmModelId ?? undefined }),
  });
}

export function getModelStatus(modelId: string): Promise<ModelStatusResponse> {
  return apiClient<ModelStatusResponse>(`/models/${modelId}`);
}
