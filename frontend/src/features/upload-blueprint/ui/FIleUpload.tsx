"use client";

import { useCallback, useRef, useState } from "react";

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const ACCEPT = ".png,.jpg,.jpeg,.pdf";

export default function FileUpload({ onFileSelected, disabled }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setFileName(file.name);
      if (file.type.startsWith("image/")) {
        const url = URL.createObjectURL(file);
        setPreview(url);
      } else {
        setPreview(null);
      }
      onFileSelected(file);
    },
    [onFileSelected],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const onDragLeave = useCallback(() => setDragActive(false), []);

  const onChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="space-y-3">
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`group relative w-full overflow-hidden rounded-sm border border-dashed p-8 text-center transition-all
          ${
            dragActive
              ? "border-cyan-400 bg-cyan-500/10 shadow-[0_0_0_1px_rgba(34,211,238,0.3),0_0_30px_-8px_rgba(34,211,238,0.5)]"
              : "border-zinc-700 bg-zinc-900/40 hover:border-zinc-500 hover:bg-zinc-900/60"
          }
          ${disabled ? "cursor-not-allowed opacity-40" : "cursor-pointer"}`}
      >
        <div className="pointer-events-none absolute inset-0 opacity-30">
          <div className="absolute left-2 top-2 h-3 w-3 border-l border-t border-cyan-400/50" />
          <div className="absolute right-2 top-2 h-3 w-3 border-r border-t border-cyan-400/50" />
          <div className="absolute bottom-2 left-2 h-3 w-3 border-b border-l border-cyan-400/50" />
          <div className="absolute bottom-2 right-2 h-3 w-3 border-b border-r border-cyan-400/50" />
        </div>

        <svg
          className={`mx-auto h-8 w-8 transition-colors ${
            dragActive ? "text-cyan-400" : "text-zinc-500 group-hover:text-zinc-300"
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.2}
            d="M12 16V4m0 0l-4 4m4-4l4 4M4 20h16"
          />
        </svg>
        <p className="mt-3 text-xs text-zinc-300">
          ドラッグ&ドロップ or クリック
        </p>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-zinc-500">
          PNG / JPG / PDF
        </p>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={onChange}
      />

      {preview && (
        <div className="overflow-hidden rounded-sm border border-zinc-800 bg-zinc-950">
          <img
            src={preview}
            alt={fileName ?? "アップロード画像"}
            className="h-auto w-full object-contain"
          />
        </div>
      )}

      {fileName && (
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-cyan-400">▸</span>
          <span className="truncate text-zinc-400">{fileName}</span>
        </div>
      )}
    </div>
  );
}
