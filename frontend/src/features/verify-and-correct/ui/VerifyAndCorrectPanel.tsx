"use client";

import type {
  Discrepancy,
  DiscrepancySeverity,
  VerificationResult,
} from "@/entities/cad-model/model/types";

interface VerifyAndCorrectPanelProps {
  verification: VerificationResult | null;
  isProcessing: boolean;
  onRun: () => void;
  disabled?: boolean;
}

const SEVERITY_COLOR: Record<DiscrepancySeverity, string> = {
  critical: "text-red-400 border-red-500/40 bg-red-500/5",
  major: "text-yellow-400 border-yellow-500/40 bg-yellow-500/5",
  minor: "text-zinc-300 border-zinc-700 bg-zinc-900/40",
};

export function VerifyAndCorrectPanel({
  verification,
  isProcessing,
  onRun,
  disabled,
}: VerifyAndCorrectPanelProps) {
  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={onRun}
        disabled={disabled || isProcessing}
        className="w-full rounded-sm border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 font-mono text-xs uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-400 hover:bg-cyan-500/20 hover:text-cyan-200 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-zinc-900/40 disabled:text-zinc-600"
      >
        {isProcessing ? "▸ Verifying…" : "▸ Verify & Auto-Correct"}
      </button>

      {verification && <VerificationSummary result={verification} />}
    </div>
  );
}

function VerificationSummary({ result }: { result: VerificationResult }) {
  const statusColor = result.is_valid
    ? "text-emerald-400 border-emerald-500/40 bg-emerald-500/5"
    : "text-red-400 border-red-500/40 bg-red-500/5";

  return (
    <div className="space-y-2">
      <div
        className={`flex items-center justify-between rounded-sm border px-3 py-2 ${statusColor}`}
      >
        <span className="font-mono text-[11px] uppercase tracking-widest">
          {result.is_valid ? "VALID" : "DIFFERENCES FOUND"}
        </span>
        <div className="flex gap-2 font-mono text-[10px]">
          <span>C:{result.critical_count}</span>
          <span>M:{result.major_count}</span>
          <span>m:{result.minor_count}</span>
        </div>
      </div>

      {result.discrepancies.length > 0 && (
        <ul className="space-y-1.5">
          {result.discrepancies.map((d, i) => (
            <li key={i}>
              <DiscrepancyItem discrepancy={d} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function DiscrepancyItem({ discrepancy }: { discrepancy: Discrepancy }) {
  return (
    <div
      className={`space-y-1 rounded-sm border px-3 py-2 ${SEVERITY_COLOR[discrepancy.severity]}`}
    >
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest">
        <span>{discrepancy.severity}</span>
        <span className="opacity-70">{discrepancy.feature_type}</span>
      </div>
      <p className="font-mono text-[11px] leading-relaxed">
        {discrepancy.description}
      </p>
      <p className="font-mono text-[10px] opacity-70">
        期待: {discrepancy.expected} / 現状: {discrepancy.actual}
      </p>
      {(discrepancy.location_hint || discrepancy.dimension_hint) && (
        <p className="font-mono text-[10px] opacity-60">
          {discrepancy.location_hint && `位置: ${discrepancy.location_hint}`}
          {discrepancy.location_hint && discrepancy.dimension_hint && " · "}
          {discrepancy.dimension_hint && `寸法: ${discrepancy.dimension_hint}`}
        </p>
      )}
    </div>
  );
}
