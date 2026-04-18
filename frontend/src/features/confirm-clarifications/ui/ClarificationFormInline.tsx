"use client";

import { useState } from "react";
import type { Clarification } from "@/entities/cad-model/model/types";

interface ClarificationFormInlineProps {
  clarifications: Clarification[];
  onConfirm: (responses: Record<string, string>) => Promise<void>;
  isLoading?: boolean;
}

export function ClarificationFormInline({
  clarifications,
  onConfirm,
  isLoading = false,
}: ClarificationFormInlineProps) {
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    try {
      setError(null);
      await onConfirm(responses);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    }
  };

  const isAllAnswered = clarifications.every((c) => responses[c.id]?.trim());

  return (
    <>
      <div className="border-b border-zinc-800 pb-4 mb-4">
        <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-yellow-400 mb-1">
          ⚠ Confirmation Required
        </h2>
        <p className="font-mono text-xs text-zinc-400">
          図面を参考に、以下の質問にお答えください
        </p>
      </div>

      <div className="space-y-4">
        {clarifications.map((clarification, index) => (
          <div
            key={clarification.id}
            className="border-l-2 border-yellow-500/40 pl-3 py-1"
          >
            <div className="flex items-start gap-2 mb-1">
              <span className="font-mono text-xs font-bold text-yellow-400 mt-0.5 flex-shrink-0">
                Q{index + 1}
              </span>
              <p className="font-mono text-xs text-zinc-100 leading-relaxed">
                {clarification.question}
              </p>
            </div>

            {clarification.suggested_answer && (
              <div className="ml-5 mb-2 font-mono text-xs text-zinc-500 bg-zinc-800/50 rounded px-2 py-1">
                💡 <span className="text-yellow-400">{clarification.suggested_answer}</span>
              </div>
            )}

            <div className="ml-5">
              <input
                type="text"
                placeholder="回答を入力..."
                value={responses[clarification.id] || ""}
                onChange={(e) =>
                  setResponses({
                    ...responses,
                    [clarification.id]: e.target.value,
                  })
                }
                disabled={isLoading}
                className="w-full font-mono text-xs px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500/50 disabled:bg-zinc-900 disabled:opacity-50 text-zinc-100 placeholder-zinc-600"
              />
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="mt-4 p-2 bg-red-500/5 border-l-2 border-red-500 pl-2">
          <p className="font-mono text-xs text-red-400">✗ {error}</p>
        </div>
      )}

      <button
        onClick={handleConfirm}
        disabled={isLoading || !isAllAnswered}
        className="w-full mt-4 font-mono text-xs font-bold uppercase tracking-wider px-3 py-2 rounded bg-yellow-600 text-zinc-900 hover:bg-yellow-500 disabled:bg-zinc-700 disabled:text-zinc-500 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? "処理中…" : "すべて確認しました →"}
      </button>
    </>
  );
}
