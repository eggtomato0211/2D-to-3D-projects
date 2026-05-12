"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { ChatMessage } from "@/features/chat-edit/model/types";

interface ChatEditPanelProps {
  messages: ChatMessage[];
  onSend: (instruction: string) => void;
  disabled?: boolean;
  isProcessing: boolean;
}

const ROLE_LABEL: Record<ChatMessage["role"], string> = {
  user: "YOU",
  assistant: "AI",
  system: "SYS",
};

const ROLE_COLOR: Record<ChatMessage["role"], string> = {
  user: "text-cyan-400",
  assistant: "text-emerald-400",
  system: "text-zinc-500",
};

export function ChatEditPanel({
  messages,
  onSend,
  disabled,
  isProcessing,
}: ChatEditPanelProps) {
  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  // 新メッセージ追加時は末尾までスクロール
  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const handleSubmit = useCallback(() => {
    const text = input.trim();
    if (!text || disabled || isProcessing) return;
    onSend(text);
    setInput("");
  }, [input, onSend, disabled, isProcessing]);

  return (
    <div className="flex h-full flex-col gap-2">
      <div
        ref={listRef}
        className="flex-1 space-y-2 overflow-y-auto rounded-sm border border-zinc-800 bg-zinc-950/60 p-3"
        style={{ minHeight: 140, maxHeight: 280 }}
      >
        {messages.length === 0 && (
          <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-600">
            例) 中央の穴を 1mm 大きく / 上面のフィレットを R2 に / スロットを 8mm 長く
          </p>
        )}
        {messages.map((m) => (
          <MessageItem key={m.id} message={m} />
        ))}
      </div>

      <div className="flex gap-1.5">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="モデルへの指示を入力 (Enter で送信)"
          disabled={disabled || isProcessing}
          className="flex-1 rounded-sm border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-xs text-zinc-100 outline-none transition-colors focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-400/30 disabled:cursor-not-allowed disabled:opacity-40"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || isProcessing || input.trim().length === 0}
          className="rounded-sm border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 font-mono text-xs uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-400 hover:bg-cyan-500/20 hover:text-cyan-200 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-transparent disabled:text-zinc-600"
        >
          {isProcessing ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

function MessageItem({ message }: { message: ChatMessage }) {
  const isError = message.status === "error";
  const isPending = message.status === "pending";

  return (
    <div className="space-y-0.5">
      <div className="flex items-baseline justify-between gap-2">
        <span
          className={`font-mono text-[9px] uppercase tracking-widest ${ROLE_COLOR[message.role]}`}
        >
          {ROLE_LABEL[message.role]}
        </span>
        {isPending && (
          <span className="font-mono text-[9px] uppercase tracking-widest text-zinc-600">
            sending…
          </span>
        )}
        {isError && (
          <span className="font-mono text-[9px] uppercase tracking-widest text-red-400">
            error
          </span>
        )}
      </div>
      <p
        className={`whitespace-pre-wrap font-mono text-[11px] leading-relaxed ${
          isError ? "text-red-300" : "text-zinc-200"
        }`}
      >
        {message.content}
      </p>
      {message.error && (
        <p className="font-mono text-[10px] leading-relaxed text-red-400">
          {message.error}
        </p>
      )}
    </div>
  );
}
