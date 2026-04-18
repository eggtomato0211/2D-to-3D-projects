import { apiClient } from "@/shared/api/base";
import type { GenerateResponse, ModelStatusResponse } from "@/entities/cad-model/model/types";

export function generateCad(blueprintId: string): Promise<GenerateResponse> {
  return apiClient<GenerateResponse>(`/blueprints/${blueprintId}/generate`, {
    method: "POST",
  });
}

export function testGenerate(): Promise<GenerateResponse> {
  return apiClient<GenerateResponse>("/test/generate", {
    method: "POST",
  });
}

export function getModelStatus(modelId: string): Promise<ModelStatusResponse> {
  return apiClient<ModelStatusResponse>(`/models/${modelId}`);
}
