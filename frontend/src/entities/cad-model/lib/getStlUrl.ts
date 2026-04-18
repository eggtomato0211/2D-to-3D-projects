import { API_BASE } from "@/shared/api/base";

export function getStlUrl(stlPath: string): string {
  return `${API_BASE}/files/${stlPath}`;
}
