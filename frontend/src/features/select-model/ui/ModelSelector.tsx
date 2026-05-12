"use client";

import { useEffect, useState } from "react";

import {
  listVlmModels,
  type VlmModelInfo,
} from "@/features/select-model/api/vlmModels";

interface ModelSelectorProps {
  value: string | null;
  onChange: (modelId: string) => void;
  disabled?: boolean;
}

export function ModelSelector({ value, onChange, disabled }: ModelSelectorProps) {
  const [models, setModels] = useState<VlmModelInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listVlmModels()
      .then((res) => {
        if (cancelled) return;
        setModels(res.models);
        // 既存選択が無ければ default を初期値に
        if (value === null) {
          onChange(res.default);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "モデル一覧の取得に失敗");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [onChange, value]);

  const selected = models.find((m) => m.id === value) ?? null;

  return (
    <div className="space-y-2">
      <label className="font-mono text-[10px] uppercase tracking-widest text-zinc-500">
        VLM Model
      </label>
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || models.length === 0}
        className="w-full appearance-none rounded-sm border border-zinc-800 bg-zinc-900/60 px-3 py-2 font-mono text-xs text-zinc-200 focus:border-cyan-500/60 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
      >
        {models.map((m) => (
          <option key={m.id} value={m.id} className="bg-zinc-900">
            {m.label}
          </option>
        ))}
      </select>
      {selected && (
        <p className="font-mono text-[10px] leading-relaxed text-zinc-500">
          {selected.description}
        </p>
      )}
      {error && (
        <p className="font-mono text-[10px] text-red-400">{error}</p>
      )}
    </div>
  );
}
