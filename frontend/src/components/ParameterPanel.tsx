"use client";

import { useState, useCallback } from "react";
import type { ParameterData } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  length: "長さ",
  radius: "半径",
  bounding_x: "全幅 (X)",
  bounding_y: "奥行 (Y)",
  bounding_z: "高さ (Z)",
};

interface ParameterPanelProps {
  parameters: ParameterData[];
  onApply: (parameters: ParameterData[]) => void;
  onHover: (param: ParameterData | null) => void;
  disabled?: boolean;
}

export default function ParameterPanel({
  parameters,
  onApply,
  onHover,
  disabled = false,
}: ParameterPanelProps) {
  const [edited, setEdited] = useState<ParameterData[]>(parameters);
  const [hasChanges, setHasChanges] = useState(false);

  // parameters が外部から変わった場合にリセット
  const [prevParams, setPrevParams] = useState(parameters);
  if (parameters !== prevParams) {
    setPrevParams(parameters);
    setEdited(parameters);
    setHasChanges(false);
  }

  const handleChange = useCallback(
    (index: number, value: string) => {
      const num = parseFloat(value);
      if (isNaN(num) || num < 0) return;

      setEdited((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], value: num };
        return next;
      });
      setHasChanges(true);
    },
    []
  );

  const handleApply = useCallback(() => {
    onApply(edited);
  }, [edited, onApply]);

  const handleReset = useCallback(() => {
    setEdited(parameters);
    setHasChanges(false);
  }, [parameters]);

  if (parameters.length === 0) return null;

  // バウンディングボックスとその他に分離
  const boundingParams = edited.filter((p) =>
    p.parameter_type.startsWith("bounding_")
  );
  const dimensionParams = edited.filter(
    (p) => !p.parameter_type.startsWith("bounding_")
  );

  return (
    <div className="space-y-4">
      <h3 className="text-base font-semibold">パラメータ</h3>

      {/* バウンディングボックス */}
      {boundingParams.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-gray-500">
            バウンディングボックス
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
                />
              );
            })}
          </div>
        </div>
      )}

      {/* 寸法パラメータ */}
      {dimensionParams.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-gray-500">寸法</p>
          <div className="space-y-2">
            {dimensionParams.map((param) => {
              const idx = edited.indexOf(param);
              const original = parameters.find((p) => p.name === param.name);
              return (
                <ParameterInput
                  key={param.name}
                  label={param.name}
                  typeLabel={TYPE_LABELS[param.parameter_type] ?? param.parameter_type}
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

      {/* 操作ボタン */}
      <div className="flex gap-2">
        <button
          type="button"
          disabled={!hasChanges || disabled}
          onClick={handleApply}
          className="flex-1 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          {disabled ? "適用中…" : "適用"}
        </button>
        <button
          type="button"
          disabled={!hasChanges || disabled}
          onClick={handleReset}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          リセット
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
}: {
  label: string;
  typeLabel?: string;
  value: number;
  originalValue: number;
  onChange: (value: string) => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  disabled: boolean;
}) {
  const isChanged = value !== originalValue;

  return (
    <div
      className="group block cursor-pointer rounded p-1.5 transition-colors hover:bg-gray-100"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="mb-1 flex items-baseline gap-1">
        <span className="text-xs font-medium text-gray-700">{label}</span>
        {typeLabel && (
          <span className="text-[10px] text-gray-400">{typeLabel}</span>
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
          className={`w-full rounded border px-2 py-1.5 text-sm transition-colors disabled:bg-gray-100 ${
            isChanged
              ? "border-blue-400 bg-blue-50"
              : "border-gray-300 bg-white"
          }`}
        />
        <span className="text-xs text-gray-400">mm</span>
      </div>
    </div>
  );
}
