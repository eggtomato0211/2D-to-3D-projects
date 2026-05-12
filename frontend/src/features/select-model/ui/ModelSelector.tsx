"use client";

import { useEffect, useState } from "react";
import { listModels, setActiveModel, type ModelSpec } from "../api/models";

interface ModelSelectorProps {
  disabled?: boolean;
  onChange?: (modelId: string) => void;
}

export function ModelSelector({ disabled, onChange }: ModelSelectorProps) {
  const [models, setModels] = useState<ModelSpec[]>([]);
  const [active, setActive] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listModels()
      .then((data) => {
        setModels(data.models);
        setActive(data.active);
        setLoading(false);
      })
      .catch((e) => {
        setError(`Failed to load models: ${e?.message ?? e}`);
        setLoading(false);
      });
  }, []);

  const handleSelect = async (modelId: string) => {
    if (modelId === active || updating) return;
    setUpdating(true);
    setError(null);
    try {
      const r = await setActiveModel(modelId);
      setActive(r.active);
      onChange?.(r.active);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Failed: ${msg}`);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-sm border border-zinc-800 bg-zinc-950/40 px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-zinc-500">
        Loading models…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-sm border border-red-900 bg-red-950/40 px-3 py-2 font-mono text-[11px] text-red-400">
        {error}
      </div>
    );
  }

  const selected = models.find((m) => m.id === active);

  return (
    <div className="space-y-2">
      <select
        value={active}
        onChange={(e) => handleSelect(e.target.value)}
        disabled={disabled || updating}
        className="w-full rounded-sm border border-zinc-800 bg-zinc-950/60 px-3 py-2 font-mono text-xs uppercase tracking-widest text-zinc-200 transition-colors hover:border-zinc-700 focus:border-cyan-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
      >
        {models.map((m) => (
          <option key={m.id} value={m.id} className="bg-zinc-950 text-zinc-200">
            [{m.provider}] {m.label}
          </option>
        ))}
      </select>
      {selected && (
        <p className="font-mono text-[10px] leading-relaxed text-zinc-500">
          {selected.description}
        </p>
      )}
      {updating && (
        <p className="font-mono text-[10px] uppercase tracking-widest text-cyan-400">
          ▸ switching…
        </p>
      )}
    </div>
  );
}
