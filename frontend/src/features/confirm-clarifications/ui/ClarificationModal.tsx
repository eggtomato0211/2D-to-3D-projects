"use client";

import { useState } from "react";
import type {
  Clarification,
  ClarificationAnswer,
} from "@/entities/cad-model/model/types";

interface ClarificationModalProps {
  clarifications: Clarification[];
  onConfirm: (responses: Record<string, ClarificationAnswer>) => Promise<void>;
  isLoading?: boolean;
}

const CUSTOM_SENTINEL = "__custom__";

function answerLabel(answer: ClarificationAnswer): string {
  switch (answer.kind) {
    case "yes":
      return "はい";
    case "no":
      return "いいえ";
    case "custom":
      return answer.text;
  }
}

function answerKey(answer: ClarificationAnswer, index: number): string {
  return `${answer.kind}-${answer.kind === "custom" ? answer.text : ""}-${index}`;
}

function answersEqual(
  a: ClarificationAnswer | undefined,
  b: ClarificationAnswer,
): boolean {
  if (!a) return false;
  if (a.kind !== b.kind) return false;
  if (a.kind === "custom" && b.kind === "custom") return a.text === b.text;
  return true;
}

function isAnswerComplete(answer: ClarificationAnswer | undefined): boolean {
  if (!answer) return false;
  if (answer.kind === "custom") return answer.text.trim().length > 0;
  return true;
}

export default function ClarificationModal({
  clarifications,
  onConfirm,
  isLoading = false,
}: ClarificationModalProps) {
  const [answers, setAnswers] = useState<Record<string, ClarificationAnswer>>({});
  const [customDrafts, setCustomDrafts] = useState<Record<string, string>>({});
  const [customMode, setCustomMode] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const selectCandidate = (id: string, candidate: ClarificationAnswer) => {
    setCustomMode((prev) => ({ ...prev, [id]: false }));
    setAnswers((prev) => ({ ...prev, [id]: candidate }));
  };

  const enterCustomMode = (id: string) => {
    setCustomMode((prev) => ({ ...prev, [id]: true }));
    const draft = customDrafts[id] ?? "";
    setAnswers((prev) => ({ ...prev, [id]: { kind: "custom", text: draft } }));
  };

  const updateCustomText = (id: string, text: string) => {
    setCustomDrafts((prev) => ({ ...prev, [id]: text }));
    setAnswers((prev) => ({ ...prev, [id]: { kind: "custom", text } }));
  };

  const handleConfirm = async () => {
    try {
      setError(null);
      await onConfirm(answers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    }
  };

  const isAllAnswered = clarifications.every((c) => isAnswerComplete(answers[c.id]));

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="border-b border-zinc-800 bg-zinc-950 px-6 py-4">
          <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-cyan-400">
            ⚠ Design Confirmation Required
          </h2>
          <p className="font-mono text-xs text-zinc-400 mt-1">
            以下の設計仮定を確認してください
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="space-y-5">
            {clarifications.map((clarification, index) => {
              const current = answers[clarification.id];
              const inCustomMode = customMode[clarification.id] ?? false;
              const candidates = clarification.candidates ?? [];

              return (
                <div
                  key={clarification.id}
                  className="border-l-2 border-cyan-500/30 pl-4 py-2"
                >
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

                  <div className="ml-5 flex flex-wrap gap-2">
                    {candidates.map((candidate, i) => {
                      const selected =
                        !inCustomMode && answersEqual(current, candidate);
                      return (
                        <button
                          key={answerKey(candidate, i)}
                          type="button"
                          onClick={() =>
                            selectCandidate(clarification.id, candidate)
                          }
                          disabled={isLoading}
                          className={`font-mono text-sm px-4 py-1.5 rounded border transition-colors ${
                            selected
                              ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
                              : "bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500"
                          } disabled:opacity-50`}
                        >
                          {answerLabel(candidate)}
                        </button>
                      );
                    })}

                    <button
                      key={CUSTOM_SENTINEL}
                      type="button"
                      onClick={() => enterCustomMode(clarification.id)}
                      disabled={isLoading}
                      className={`font-mono text-sm px-4 py-1.5 rounded border transition-colors ${
                        inCustomMode
                          ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
                          : "bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500"
                      } disabled:opacity-50`}
                    >
                      自分で入力
                    </button>
                  </div>

                  {inCustomMode && (
                    <div className="ml-5 mt-2">
                      <input
                        type="text"
                        placeholder="回答を入力..."
                        value={customDrafts[clarification.id] ?? ""}
                        onChange={(e) =>
                          updateCustomText(clarification.id, e.target.value)
                        }
                        disabled={isLoading}
                        className="w-full font-mono text-sm px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 disabled:bg-zinc-900 disabled:opacity-50 text-zinc-100 placeholder-zinc-600"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="border-t border-zinc-800 bg-red-500/5 px-6 py-3">
            <p className="font-mono text-xs text-red-400">✗ {error}</p>
          </div>
        )}

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
