import { apiClient } from "@/shared/api/base";
import type {
  ModelStatusResponse,
  ParameterData,
} from "@/entities/cad-model/model/types";

export function updateParameters(
  modelId: string,
  parameters: ParameterData[],
): Promise<ModelStatusResponse> {
  return apiClient<ModelStatusResponse>(`/models/${modelId}/parameters`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parameters }),
  });
}
