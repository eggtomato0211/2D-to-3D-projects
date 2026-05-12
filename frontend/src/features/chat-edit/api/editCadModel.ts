import { apiClient } from "@/shared/api/base";
import type { ModelStatusResponse } from "@/entities/cad-model/model/types";

export function editCadModel(
  modelId: string,
  instruction: string,
  vlmModelId: string | null,
): Promise<ModelStatusResponse> {
  return apiClient<ModelStatusResponse>(`/models/${modelId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction, model: vlmModelId ?? undefined }),
  });
}
