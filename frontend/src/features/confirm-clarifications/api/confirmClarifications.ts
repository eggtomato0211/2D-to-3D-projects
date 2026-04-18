import { apiClient } from "@/shared/api/base";
import type { GenerateResponse } from "@/entities/cad-model/model/types";

export function confirmClarifications(
  blueprintId: string,
  modelId: string,
  responses: Record<string, string>
): Promise<GenerateResponse> {
  return apiClient<GenerateResponse>(
    `/blueprints/${blueprintId}/confirm-clarifications?model_id=${modelId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ responses }),
    }
  );
}
