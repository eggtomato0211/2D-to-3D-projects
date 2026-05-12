"use client";

interface GenerateButtonProps {
  onGenerate: () => void;
  disabled: boolean;
  isProcessing: boolean;
  hasFile: boolean;
}

export function GenerateButton({
  onGenerate,
  disabled,
  isProcessing,
  hasFile,
}: GenerateButtonProps) {
  return (
    <button
      type="button"
      disabled={!hasFile || disabled}
      onClick={onGenerate}
      className="group relative w-full overflow-hidden rounded-sm border border-cyan-500/40 bg-cyan-500/10 px-4 py-3 font-mono text-sm uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-400 hover:bg-cyan-500/20 hover:text-cyan-200 hover:shadow-[0_0_0_1px_rgba(34,211,238,0.4),0_0_24px_-6px_rgba(34,211,238,0.6)] disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-zinc-900/40 disabled:text-zinc-600 disabled:shadow-none"
    >
      <span className="relative z-10">
        {isProcessing ? "▸ 処理中…" : "▸ 3D モデル生成"}
      </span>
    </button>
  );
}
