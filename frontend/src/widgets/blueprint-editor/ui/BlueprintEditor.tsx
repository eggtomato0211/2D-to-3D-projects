"use client";

import { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";

import { StatusMessage } from "@/shared/ui/StatusMessage";
import { getStlUrl } from "@/entities/cad-model/lib/getStlUrl";
import type {
  ParameterData,
  Clarification,
  ClarificationAnswer,
} from "@/entities/cad-model/model/types";
import FileUpload from "@/features/upload-blueprint/ui/FileUpload";
import { uploadBlueprint } from "@/features/upload-blueprint/api/uploadBlueprint";
import { GenerateButton } from "@/features/generate-cad/ui/GenerateButton";
import { ModelSelector } from "@/features/select-model/ui/ModelSelector";
import {
  generateCad,
  testGenerate,
} from "@/features/generate-cad/api/generateCad";
import { ParameterPanel } from "@/features/edit-parameters/ui/ParameterPanel";
import { updateParameters } from "@/features/edit-parameters/api/updateParameters";
import { ClarificationFormInline } from "@/features/confirm-clarifications/ui/ClarificationFormInline";
import { confirmClarifications } from "@/features/confirm-clarifications/api/confirmClarifications";

const StlViewer = dynamic(
  () => import("@/entities/cad-model/ui/STLViewer"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full min-h-[400px] items-center justify-center rounded-sm border border-zinc-800 bg-zinc-950/60">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600">
          Loading viewer…
        </p>
      </div>
    ),
  },
);

type Phase = "idle" | "uploading" | "generating" | "clarifying" | "done" | "error";

const PHASE_LABEL: Record<Phase, { text: string; color: string }> = {
  idle: { text: "IDLE", color: "text-zinc-500" },
  uploading: { text: "UPLOAD", color: "text-cyan-400" },
  generating: { text: "GENERATE", color: "text-cyan-400" },
  clarifying: { text: "CLARIFY", color: "text-yellow-400" },
  done: { text: "READY", color: "text-emerald-400" },
  error: { text: "ERROR", color: "text-red-400" },
};

export function BlueprintEditor() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [stlUrl, setStlUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [modelId, setModelId] = useState<string | null>(null);
  const [blueprintId, setBlueprintId] = useState<string | null>(null);
  const [parameters, setParameters] = useState<ParameterData[]>([]);
  const [isUpdatingParams, setIsUpdatingParams] = useState(false);
  const [hoveredParam, setHoveredParam] = useState<ParameterData | null>(null);
  const [clarifications, setClarifications] = useState<Clarification[]>([]);
  const [isConfirmingClarifications, setIsConfirmingClarifications] = useState(false);
  const [blueprintPreviewUrl, setBlueprintPreviewUrl] = useState<string | null>(null);

  // File から Object URL を生成（プレビュー用）。file 変更時とアンマウント時にクリーンアップ
  useEffect(() => {
    if (!file) {
      setBlueprintPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setBlueprintPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

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
      setBlueprintId(blueprint_id);

      setPhase("generating");
      const result = await generateCad(blueprint_id);

      // Check for clarifications needed
      if (result.status === "needs_clarification" && result.clarifications) {
        setClarifications(result.clarifications);
        setModelId(result.model_id);
        setPhase("clarifying");
        return;
      }

      if (result.status === "FAILED" || result.status === "failed") {
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
        err instanceof Error ? err.message : "予期しないエラーが発生しました",
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

  const handleConfirmClarifications = useCallback(
    async (responses: Record<string, ClarificationAnswer>) => {
      if (!blueprintId || !modelId) return;

      try {
        setIsConfirmingClarifications(true);
        setErrorMessage(null);
        setPhase("generating");

        const result = await confirmClarifications(blueprintId, modelId, responses);

        if (result.status === "FAILED" || result.status === "failed") {
          setErrorMessage(result.error_message ?? "CAD生成に失敗しました");
          setPhase("error");
          return;
        }

        if (result.stl_path) {
          setStlUrl(getStlUrl(result.stl_path));
          setParameters(result.parameters ?? []);
          setPhase("done");
        } else {
          setErrorMessage("STLファイルが生成されませんでした");
          setPhase("error");
        }
      } catch (err) {
        setErrorMessage(
          err instanceof Error ? err.message : "確認処理に失敗しました",
        );
        setPhase("error");
      } finally {
        setIsConfirmingClarifications(false);
      }
    },
    [blueprintId, modelId],
  );

  const handleUpdateParameters = useCallback(
    async (newParams: ParameterData[]) => {
      if (!modelId) return;

      try {
        setIsUpdatingParams(true);
        setErrorMessage(null);
        const result = await updateParameters(modelId, newParams);

        if (result.status === "FAILED") {
          setErrorMessage(
            result.error_message ?? "パラメータ変更に失敗しました",
          );
          return;
        }

        if (result.stl_path) {
          setStlUrl(getStlUrl(result.stl_path));
          setParameters(result.parameters ?? []);
        }
      } catch (err) {
        setErrorMessage(
          err instanceof Error ? err.message : "パラメータ更新に失敗しました",
        );
      } finally {
        setIsUpdatingParams(false);
      }
    },
    [modelId],
  );

  const isProcessing = phase === "uploading" || phase === "generating" || phase === "clarifying";
  const phaseLabel = PHASE_LABEL[phase];

  return (
    <>
      <main className="mx-auto flex min-h-screen w-full max-w-[1920px] flex-col p-4 lg:h-screen lg:overflow-hidden">
      {/* ヘッダー */}
      <header className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-6 w-6 items-center justify-center rounded-sm border border-cyan-500/40 bg-cyan-500/10">
            <span className="font-mono text-[10px] font-bold text-cyan-400">
              B
            </span>
          </div>
          <div>
            <h1 className="font-mono text-sm font-semibold tracking-wider text-zinc-100">
              BLUEPRINT→CAD
            </h1>
            <p className="font-mono text-[9px] uppercase tracking-widest text-zinc-600">
              2D drawing to 3D parametric model
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-sm border border-zinc-800 bg-zinc-900/60 px-3 py-1">
          <span className={`h-1.5 w-1.5 rounded-full ${
            phase === "done" ? "bg-emerald-400" :
            phase === "error" ? "bg-red-400" :
            isProcessing ? "animate-pulse bg-cyan-400" :
            "bg-zinc-600"
          }`} />
          <span className={`font-mono text-[10px] uppercase tracking-widest ${phaseLabel.color}`}>
            {phaseLabel.text}
          </span>
        </div>
      </header>

      <div className="mt-4 grid flex-1 grid-cols-1 gap-4 lg:min-h-0 lg:grid-cols-[360px_1fr] lg:grid-rows-[minmax(0,1fr)] xl:grid-cols-[400px_1fr]">
        {/* 左カラム */}
        <aside className="panel space-y-5 overflow-y-auto rounded-sm p-4 lg:min-h-0">
            {/* 確認事項フェーズ：フォーム表示 */}
            {phase === "clarifying" && (
              <ClarificationFormInline
                clarifications={clarifications}
                onConfirm={handleConfirmClarifications}
                isLoading={isConfirmingClarifications}
              />
            )}

            {/* 通常フェーズ：コントロール表示 */}
            {phase !== "clarifying" && (
              <>
                <section className="space-y-3">
                  <SectionTitle index="01" label="Blueprint Input" />
                  <FileUpload
                    onFileSelected={handleFileSelected}
                    disabled={isProcessing}
                  />
                </section>

                <section className="space-y-3">
                  <SectionTitle index="02" label="Model" />
                  <ModelSelector disabled={isProcessing} />
                </section>

                <section className="space-y-3">
                  <SectionTitle index="03" label="Generate" />
                  <GenerateButton
                    onGenerate={handleGenerate}
                    onTestGenerate={handleTestGenerate}
                    disabled={isProcessing}
                    isProcessing={isProcessing}
                    hasFile={file !== null}
                  />

                  {phase === "uploading" && (
                    <StatusMessage text="Uploading blueprint…" />
                  )}
                  {phase === "generating" && (
                    <StatusMessage text="Generating 3D model…" />
                  )}
                  {phase === "done" && (
                    <div className="flex items-center gap-2 font-mono text-xs text-emerald-400">
                      <span>✓</span>
                      <span>Generation complete</span>
                    </div>
                  )}
                  {phase === "error" && errorMessage && (
                    <div className="space-y-2 rounded-sm border border-red-500/30 bg-red-500/5 p-3">
                      <div className="flex items-start gap-2">
                        <span className="font-mono text-xs text-red-400">!</span>
                        <p className="font-mono text-[11px] leading-relaxed text-red-300">
                          {errorMessage}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={handleGenerate}
                        className="font-mono text-[10px] uppercase tracking-widest text-cyan-400 underline-offset-2 hover:underline"
                      >
                        ▸ Retry
                      </button>
                    </div>
                  )}
                </section>

                {phase === "done" && parameters.length > 0 && (
                  <section className="space-y-3 border-t border-zinc-800 pt-4">
                    <SectionTitle index="03" label="Parametric Edit" />
                    <ParameterPanel
                      parameters={parameters}
                      onApply={handleUpdateParameters}
                      onHover={setHoveredParam}
                      disabled={isUpdatingParams}
                    />
                    {isUpdatingParams && <StatusMessage text="Applying changes…" />}
                    {errorMessage && !isProcessing && (
                      <p className="font-mono text-[10px] text-red-400">
                        {errorMessage}
                      </p>
                    )}
                  </section>
                )}
              </>
            )}
        </aside>

        {/* 右カラム: ビューア */}
        <section className="flex h-[70vh] flex-col lg:h-full lg:min-h-0">
          <div className="mb-2 flex items-center justify-between">
            <SectionTitle
              index="04"
              label={phase === "clarifying" ? "Blueprint Reference" : "3D Viewport"}
            />
            {phase === "clarifying" && blueprintPreviewUrl && (
              <span className="font-mono text-[10px] uppercase tracking-widest text-yellow-500/70">
                REFERENCE · {file?.type.includes("pdf") ? "PDF" : "IMAGE"}
              </span>
            )}
            {phase !== "clarifying" && stlUrl && (
              <span className="font-mono text-[10px] uppercase tracking-widest text-zinc-600">
                STL · OpenCASCADE
              </span>
            )}
          </div>

          <div className="panel relative flex-1 overflow-hidden rounded-sm">
            {/* コーナーデコレーション */}
            <div className="pointer-events-none absolute left-2 top-2 h-4 w-4 border-l border-t border-cyan-400/40 z-10" />
            <div className="pointer-events-none absolute right-2 top-2 h-4 w-4 border-r border-t border-cyan-400/40 z-10" />
            <div className="pointer-events-none absolute bottom-2 left-2 h-4 w-4 border-b border-l border-cyan-400/40 z-10" />
            <div className="pointer-events-none absolute bottom-2 right-2 h-4 w-4 border-b border-r border-cyan-400/40 z-10" />

            {/* 確認事項フェーズ：図面を表示 */}
            {phase === "clarifying" && blueprintPreviewUrl && file ? (
              file.type.includes("pdf") ? (
                <iframe
                  src={blueprintPreviewUrl}
                  className="h-full w-full bg-white"
                  title="Blueprint"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center overflow-auto bg-zinc-100 p-4">
                  <img
                    src={blueprintPreviewUrl}
                    alt="Blueprint"
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
              )
            ) : stlUrl ? (
              <StlViewer
                url={stlUrl}
                highlightEdgePoints={hoveredParam?.edge_points ?? null}
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-zinc-700"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z M3.27 6.96L12 12.01l8.73-5.05 M12 22.08V12"
                    />
                  </svg>
                  <p className="mt-4 font-mono text-[11px] uppercase tracking-widest text-zinc-600">
                    Awaiting input
                  </p>
                  <p className="mt-1 font-mono text-[10px] text-zinc-700">
                    Upload a blueprint to begin
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
    </>
  );
}

function SectionTitle({ index, label }: { index: string; label: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="font-mono text-[10px] text-cyan-400/70">{index}</span>
      <h2 className="font-mono text-xs uppercase tracking-widest text-zinc-200">
        {label}
      </h2>
    </div>
  );
}
