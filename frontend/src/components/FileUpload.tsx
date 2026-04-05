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
    <div className="space-y-4">
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`w-full rounded-lg border-2 border-dashed p-8 text-center transition-colors
          ${dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
          ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}`}
      >
        <svg
          className="mx-auto h-10 w-10 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 16V4m0 0l-4 4m4-4l4 4M4 20h16"
          />
        </svg>
        <p className="mt-2 text-sm text-gray-600">
          ドラッグ&ドロップ または クリックしてファイルを選択
        </p>
        <p className="mt-1 text-xs text-gray-400">PNG, JPG, PDF に対応</p>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={onChange}
      />

      {preview && (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <img
            src={preview}
            alt={fileName ?? "アップロード画像"}
            className="h-auto w-full object-contain"
          />
        </div>
      )}

      {fileName && !preview && (
        <p className="text-sm text-gray-500">選択ファイル: {fileName}</p>
      )}
    </div>
  );
}
