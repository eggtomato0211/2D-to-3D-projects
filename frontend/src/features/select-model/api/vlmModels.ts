import { apiClient } from "@/shared/api/base";

export interface VlmModelInfo {
  id: string;
  label: string;
  provider: string;
  description: string;
  default: boolean;
}

export interface VlmModelListResponse {
  models: VlmModelInfo[];
  default: string;
}

export function listVlmModels(): Promise<VlmModelListResponse> {
  return apiClient<VlmModelListResponse>("/vlm-models");
}
