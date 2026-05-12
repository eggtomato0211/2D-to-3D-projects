import { apiClient } from "@/shared/api/base";
import type {
  ClarificationAnswer,
  GenerateResponse,
} from "@/entities/cad-model/model/types";

export function confirmClarifications(
  blueprintId: string,
  modelId: string,
  responses: Record<string, ClarificationAnswer>,
  vlmModelId: string | null,
): Promise<GenerateResponse> {
  return apiClient<GenerateResponse>(
    `/blueprints/${blueprintId}/confirm-clarifications?model_id=${modelId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ responses, model: vlmModelId ?? undefined }),
    },
  );
}
