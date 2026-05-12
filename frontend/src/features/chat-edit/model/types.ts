export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  /** "送信中" / "成功" / "失敗" などのステータス */
  status?: "pending" | "ok" | "error";
  /** 失敗時のエラーメッセージ */
  error?: string;
}
