"use client";

import { useState } from "react";
import type { Clarification } from "@/entities/cad-model/model/types";

interface ClarificationModalProps {
  clarifications: Clarification[];
  onConfirm: (responses: Record<string, string>) => Promise<void>;
  isLoading?: boolean;
}

export default function ClarificationModal({
  clarifications,
  onConfirm,
  isLoading = false,
}: ClarificationModalProps) {
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
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* ヘッダー */}
        <div className="border-b border-zinc-800 bg-zinc-950 px-6 py-4">
          <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-cyan-400">
            ⚠ Design Confirmation Required
          </h2>
          <p className="font-mono text-xs text-zinc-400 mt-1">
            以下の設計仮定を確認してください
          </p>
        </div>

        {/* コンテンツ */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="space-y-5">
            {clarifications.map((clarification, index) => (
              <div
                key={clarification.id}
                className="border-l-2 border-cyan-500/30 pl-4 py-2"
              >
                {/* 質問番号と質問文 */}
                <div className="mb-2">
                  <div className="flex items-start gap-2">
                    <span className="font-mono text-xs font-bold text-cyan-400 mt-0.5">
                      Q{index + 1}.
                    </span>
                    <p className="font-mono text-sm text-zinc-100 leading-relaxed">
                      {clarification.question}
                    </p>
                  </div>
                </div>

                {/* 推奨値表示 */}
                {clarification.suggested_answer && (
                  <div className="ml-5 mb-3 font-mono text-xs text-zinc-500 bg-zinc-800/50 rounded px-2 py-1">
                    💡 推奨: <span className="text-cyan-400">{clarification.suggested_answer}</span>
                  </div>
                )}

                {/* 入力フィールド */}
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
                    className="w-full font-mono text-sm px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 disabled:bg-zinc-900 disabled:opacity-50 text-zinc-100 placeholder-zinc-600"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="border-t border-zinc-800 bg-red-500/5 px-6 py-3">
            <p className="font-mono text-xs text-red-400">✗ {error}</p>
          </div>
        )}

        {/* フッター */}
        <div className="border-t border-zinc-800 bg-zinc-950 px-6 py-4 flex gap-3">
          <button
            onClick={handleConfirm}
            disabled={isLoading || !isAllAnswered}
            className="flex-1 font-mono text-sm font-bold uppercase tracking-wider px-4 py-2 rounded bg-cyan-600 text-zinc-900 hover:bg-cyan-500 disabled:bg-zinc-700 disabled:text-zinc-500 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? "処理中…" : "確認して進む →"}
          </button>
        </div>
      </div>
    </div>
  );
}

