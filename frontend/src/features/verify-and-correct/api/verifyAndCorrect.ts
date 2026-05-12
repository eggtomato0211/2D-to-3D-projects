import { apiClient } from "@/shared/api/base";
import type { ModelStatusResponse } from "@/entities/cad-model/model/types";

export function verifyAndCorrect(
  modelId: string,
  vlmModelId: string | null,
): Promise<ModelStatusResponse> {
  return apiClient<ModelStatusResponse>(
    `/models/${modelId}/verify-and-correct`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: vlmModelId ?? undefined }),
    },
  );
}
