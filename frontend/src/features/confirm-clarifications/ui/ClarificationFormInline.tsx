"use client";

import { useState } from "react";
import type {
  Clarification,
  ClarificationAnswer,
} from "@/entities/cad-model/model/types";

interface ClarificationFormInlineProps {
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

export function ClarificationFormInline({
  clarifications,
  onConfirm,
  isLoading = false,
}: ClarificationFormInlineProps) {
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
        {clarifications.map((clarification, index) => {
          const current = answers[clarification.id];
          const inCustomMode = customMode[clarification.id] ?? false;
          const candidates = clarification.candidates ?? [];

          return (
            <div
              key={clarification.id}
              className="border-l-2 border-yellow-500/40 pl-3 py-1"
            >
              <div className="flex items-start gap-2 mb-2">
                <span className="font-mono text-xs font-bold text-yellow-400 mt-0.5 flex-shrink-0">
                  Q{index + 1}
                </span>
                <p className="font-mono text-xs text-zinc-100 leading-relaxed">
                  {clarification.question}
                </p>
              </div>

              <div className="ml-5 flex flex-wrap gap-2">
                {candidates.map((candidate, i) => {
                  const selected = !inCustomMode && answersEqual(current, candidate);
                  return (
                    <button
                      key={answerKey(candidate, i)}
                      type="button"
                      onClick={() => selectCandidate(clarification.id, candidate)}
                      disabled={isLoading}
                      className={`font-mono text-xs px-3 py-1.5 rounded border transition-colors ${
                        selected
                          ? "bg-yellow-500/20 border-yellow-500 text-yellow-300"
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
                  className={`font-mono text-xs px-3 py-1.5 rounded border transition-colors ${
                    inCustomMode
                      ? "bg-yellow-500/20 border-yellow-500 text-yellow-300"
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
                    className="w-full font-mono text-xs px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500/50 disabled:bg-zinc-900 disabled:opacity-50 text-zinc-100 placeholder-zinc-600"
                  />
                </div>
              )}
            </div>
          );
        })}
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
