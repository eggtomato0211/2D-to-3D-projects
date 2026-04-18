"use client";

import { useState, useCallback } from "react";
import type { ParameterData } from "@/entities/cad-model/model/types";

const TYPE_LABELS: Record<string, string> = {
  length: "長さ",
  radius: "半径",
  bounding_x: "X",
  bounding_y: "Y",
  bounding_z: "Z",
};

interface ParameterPanelProps {
  parameters: ParameterData[];
  onApply: (parameters: ParameterData[]) => void;
  onHover: (param: ParameterData | null) => void;
  disabled?: boolean;
}

export function ParameterPanel({
  parameters,
  onApply,
  onHover,
  disabled = false,
}: ParameterPanelProps) {
  const [edited, setEdited] = useState<ParameterData[]>(parameters);
  const [hasChanges, setHasChanges] = useState(false);

  const [prevParams, setPrevParams] = useState(parameters);
  if (parameters !== prevParams) {
    setPrevParams(parameters);
    setEdited(parameters);
    setHasChanges(false);
  }

  const handleChange = useCallback((index: number, value: string) => {
    const num = parseFloat(value);
    if (isNaN(num) || num < 0) return;

    setEdited((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], value: num };
      return next;
    });
    setHasChanges(true);
  }, []);

  const handleApply = useCallback(() => {
    onApply(edited);
  }, [edited, onApply]);

  const handleReset = useCallback(() => {
    setEdited(parameters);
    setHasChanges(false);
  }, [parameters]);

  if (parameters.length === 0) return null;

  const boundingParams = edited.filter((p) =>
    p.parameter_type.startsWith("bounding_"),
  );
  const dimensionParams = edited.filter(
    (p) => !p.parameter_type.startsWith("bounding_"),
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <h3 className="font-mono text-xs uppercase tracking-widest text-zinc-400">
          ▸ Parameters
        </h3>
        <span className="font-mono text-[10px] uppercase tracking-widest text-zinc-600">
          {edited.length} items
        </span>
      </div>

      {boundingParams.length > 0 && (
        <div className="space-y-2">
          <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-500">
            Bounding Box
          </p>
          <div className="grid grid-cols-3 gap-2">
            {boundingParams.map((param) => {
              const idx = edited.indexOf(param);
              const original = parameters.find((p) => p.name === param.name);
              return (
                <ParameterInput
                  key={param.name}
                  label={TYPE_LABELS[param.parameter_type] ?? param.name}
                  value={param.value}
                  originalValue={original?.value ?? param.value}
                  onChange={(v) => handleChange(idx, v)}
                  onMouseEnter={() => onHover(original ?? param)}
                  onMouseLeave={() => onHover(null)}
                  disabled={disabled}
                  compact
                />
              );
            })}
          </div>
        </div>
      )}

      {dimensionParams.length > 0 && (
        <div className="space-y-2">
          <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-500">
            Dimensions
          </p>
          <div className="space-y-1.5">
            {dimensionParams.map((param) => {
              const idx = edited.indexOf(param);
              const original = parameters.find((p) => p.name === param.name);
              return (
                <ParameterInput
                  key={param.name}
                  label={param.name}
                  typeLabel={
                    TYPE_LABELS[param.parameter_type] ?? param.parameter_type
                  }
                  value={param.value}
                  originalValue={original?.value ?? param.value}
                  onChange={(v) => handleChange(idx, v)}
                  onMouseEnter={() => onHover(original ?? param)}
                  onMouseLeave={() => onHover(null)}
                  disabled={disabled}
                />
              );
            })}
          </div>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <button
          type="button"
          disabled={!hasChanges || disabled}
          onClick={handleApply}
          className="flex-1 rounded-sm border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 font-mono text-xs uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-400 hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-transparent disabled:text-zinc-600"
        >
          {disabled ? "Applying…" : "Apply"}
        </button>
        <button
          type="button"
          disabled={!hasChanges || disabled}
          onClick={handleReset}
          className="rounded-sm border border-zinc-800 bg-transparent px-3 py-2 font-mono text-xs uppercase tracking-widest text-zinc-500 transition-colors hover:border-zinc-600 hover:text-zinc-300 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Reset
        </button>
      </div>
    </div>
  );
}

function ParameterInput({
  label,
  typeLabel,
  value,
  originalValue,
  onChange,
  onMouseEnter,
  onMouseLeave,
  disabled,
  compact = false,
}: {
  label: string;
  typeLabel?: string;
  value: number;
  originalValue: number;
  onChange: (value: string) => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  disabled: boolean;
  compact?: boolean;
}) {
  const isChanged = value !== originalValue;

  return (
    <div
      className="group rounded-sm px-2 py-1.5 transition-colors hover:bg-zinc-800/40"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className={`mb-1 flex items-baseline gap-1.5 ${compact ? "justify-center" : ""}`}>
        <span className="font-mono text-[11px] text-zinc-300">{label}</span>
        {typeLabel && (
          <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-600">
            {typeLabel}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1">
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          step="any"
          min="0"
          className={`w-full rounded-sm border bg-zinc-950 px-2 py-1 font-mono text-xs text-zinc-100 outline-none transition-colors focus:ring-1 disabled:opacity-50 ${
            isChanged
              ? "border-cyan-500/60 focus:border-cyan-400 focus:ring-cyan-400/30"
              : "border-zinc-800 focus:border-zinc-600 focus:ring-zinc-600/30"
          }`}
        />
        <span className="font-mono text-[10px] text-zinc-600">mm</span>
      </div>
    </div>
  );
}
