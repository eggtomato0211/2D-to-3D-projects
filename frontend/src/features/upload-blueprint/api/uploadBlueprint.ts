import { apiClient } from "@/shared/api/base";
import type { UploadResponse } from "@/entities/blueprint/model/types";

export function uploadBlueprint(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return apiClient<UploadResponse>("/blueprints/upload", {
    method: "POST",
    body: form,
  });
}