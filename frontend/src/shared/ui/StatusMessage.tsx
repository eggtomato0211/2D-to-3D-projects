"use client";

interface StatusMessageProps {
  text: string;
}

export function StatusMessage({ text }: StatusMessageProps) {
  return (
    <div className="flex items-center gap-2 text-xs text-cyan-300/80">
      <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
          className="opacity-20"
        />
        <path
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"
          className="opacity-80"
        />
      </svg>
      <span className="font-mono">{text}</span>
    </div>
  );
}
