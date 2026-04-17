"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import FileUpload from "@/components/FileUpload";
import ParameterPanel from "@/components/ParameterPanel";
import {
  uploadBlueprint,
  generateCad,
  testGenerate,
  updateParameters,
  getStlUrl,
} from "@/lib/api";
import type { ParameterData } from "@/lib/api";

const StlViewer = dynamic(() => import("@/components/StlViewer"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[400px] items-center justify-center rounded-lg border border-gray-200 bg-gray-50">
      <p className="text-gray-400">3D ビューアを読み込み中…</p>
    </div>
  ),
});

type Phase = "idle" | "uploading" | "generating" | "done" | "error";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [stlUrl, setStlUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [modelId, setModelId] = useState<string | null>(null);
  const [parameters, setParameters] = useState<ParameterData[]>([]);
  const [isUpdatingParams, setIsUpdatingParams] = useState(false);
  const [hoveredParam, setHoveredParam] = useState<ParameterData | null>(null);

  const handleFileSelected = useCallback((f: File) => {
    setFile(f);
    setStlUrl(null);
    setErrorMessage(null);
    setModelId(null);
    setParameters([]);
    setPhase("idle");
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!file) return;

    try {
      setPhase("uploading");
      setErrorMessage(null);
      const { blueprint_id } = await uploadBlueprint(file);

      setPhase("generating");
      const result = await generateCad(blueprint_id);

      if (result.status === "FAILED") {
        setErrorMessage(result.error_message ?? "CAD生成に失敗しました");
        setPhase("error");
        return;
      }

      if (result.stl_path) {
        setStlUrl(getStlUrl(result.stl_path));
        setModelId(result.model_id);
        setParameters(result.parameters ?? []);
        setPhase("done");
      } else {
        setErrorMessage("STLファイルが生成されませんでした");
        setPhase("error");
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "予期しないエラーが発生しました"
      );
      setPhase("error");
    }
  }, [file]);

  const handleTestGenerate = useCallback(async () => {
    try {
      setPhase("generating");
      setErrorMessage(null);
      const result = await testGenerate();
      if (result.stl_path) {
        setStlUrl(getStlUrl(result.stl_path));
        setModelId(result.model_id);
        setParameters(result.parameters ?? []);
        setPhase("done");
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "テスト生成に失敗");
      setPhase("error");
    }
  }, []);

  const handleUpdateParameters = useCallback(
    async (newParams: ParameterData[]) => {
      if (!modelId) return;

      try {
        setIsUpdatingParams(true);
        setErrorMessage(null);
        const result = await updateParameters(modelId, newParams);

        if (result.status === "FAILED") {
          setErrorMessage(
            result.error_message ?? "パラメータ変更に失敗しました"
          );
          return;
        }

        if (result.stl_path) {
          setStlUrl(getStlUrl(result.stl_path));
          setParameters(result.parameters ?? []);
        }
      } catch (err) {
        setErrorMessage(
          err instanceof Error ? err.message : "パラメータ更新に失敗しました"
        );
      } finally {
        setIsUpdatingParams(false);
      }
    },
    [modelId]
  );

  const isProcessing = phase === "uploading" || phase === "generating";

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1920px] flex-col gap-6 p-6 lg:h-screen lg:overflow-hidden">
      <h1 className="text-2xl font-bold">Blueprint to CAD</h1>

      <div className="grid flex-1 grid-cols-1 gap-6 lg:min-h-0 lg:grid-cols-[360px_1fr] lg:grid-rows-[minmax(0,1fr)] xl:grid-cols-[400px_1fr]">
        {/* 左カラム: アップロード + パラメータ */}
        <div className="space-y-6 lg:min-h-0 lg:overflow-y-auto lg:pr-2">
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">図面アップロード</h2>

            <FileUpload
              onFileSelected={handleFileSelected}
              disabled={isProcessing}
            />

            <button
              type="button"
              disabled={!file || isProcessing}
              onClick={handleGenerate}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
              {isProcessing ? "処理中…" : "3Dモデルを生成"}
            </button>

            <button
              type="button"
              disabled={isProcessing}
              onClick={handleTestGenerate}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              テスト生成（固定モデル）
            </button>

            {/* ステータス表示 */}
            {phase === "uploading" && (
              <StatusMessage text="図面をアップロード中…" />
            )}
            {phase === "generating" && (
              <StatusMessage text="3Dモデルを生成中… しばらくお待ちください" />
            )}
            {phase === "done" && (
              <p className="text-sm font-medium text-green-600">生成完了</p>
            )}
            {phase === "error" && (
              <div className="space-y-2">
                <p className="text-sm text-red-600">{errorMessage}</p>
                <button
                  type="button"
                  onClick={handleGenerate}
                  className="text-sm font-medium text-blue-600 underline hover:text-blue-800"
                >
                  リトライ
                </button>
              </div>
            )}
          </div>

          {/* パラメータパネル */}
          {phase === "done" && parameters.length > 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <ParameterPanel
                parameters={parameters}
                onApply={handleUpdateParameters}
                onHover={setHoveredParam}
                disabled={isUpdatingParams}
              />
              {isUpdatingParams && (
                <div className="mt-3">
                  <StatusMessage text="パラメータを適用中…" />
                </div>
              )}
              {errorMessage && !isProcessing && phase === "done" && (
                <p className="mt-2 text-xs text-red-500">{errorMessage}</p>
              )}
            </div>
          )}
        </div>

        {/* 右カラム: 3Dビューア */}
        <div className="flex h-[70vh] flex-col lg:h-full lg:min-h-0">
          <h2 className="mb-4 text-lg font-semibold">3Dモデル</h2>

          <div className="relative flex-1">
            {stlUrl ? (
              <StlViewer
                url={stlUrl}
                highlightEdgePoints={hoveredParam?.edge_points ?? null}
              />
            ) : (
              <div className="flex h-full items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50">
                <p className="text-gray-400">
                  図面をアップロードして生成ボタンを押してください
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

function StatusMessage({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-600">
      <svg
        className="h-4 w-4 animate-spin"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
          className="opacity-25"
        />
        <path
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"
          className="opacity-75"
        />
      </svg>
      {text}
    </div>
  );
}
