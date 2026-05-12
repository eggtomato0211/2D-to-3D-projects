"""§ option b: Verifier-Corrector ループありで CADPrompt を走らせる。

我々の独自貢献である Phase 2 検証ループの効果を、CADPrompt ベンチマーク上で定量化する。

各エントリで:
  1. GT STL を 4 視点線画にレンダして「blueprint」とする
  2. 自然言語 prompt から初期 CadQuery 生成（runner.py と同じ）
  3. 実行 → 初期 STL
  4. VerifyAndCorrectUseCase（ループ）を回す
  5. 最終 STL を GT STL と比較
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import traceback
import uuid
from pathlib import Path

import numpy as np

EXPERIMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = EXPERIMENT_DIR / "data"
OUTPUT_DIR = EXPERIMENT_DIR / "output"

# --- 既存の runner からヘルパ流用 -----------------------------------------
sys.path.insert(0, str(EXPERIMENT_DIR))
from runner import (  # noqa: E402
    list_entries,
    load_entry,
    compute_metrics,
)

# --- backend モジュール ---------------------------------------------------
sys.path.insert(0, "/app")


def render_gt_blueprint(gt_stl_path: str, gt_step_path: str | None,
                       blueprint_save_path: Path) -> Path:
    """GT STL を 4 視点線画にレンダして 1 枚画像（iso）に保存。

    blueprint として VLM に渡す用途。
    """
    from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer
    from app.infrastructure.rendering.trimesh_pyrender_renderer import (
        TrimeshPyrenderRenderer,
    )

    if gt_step_path and Path(gt_step_path).exists():
        line_renderer = CadQuerySvgRenderer()
        views = line_renderer.render(gt_step_path)
        blueprint_save_path.write_bytes(views.iso)
    else:
        # STEP が無い場合は STL から影付きレンダ（妥協策）
        shaded_renderer = TrimeshPyrenderRenderer()
        views = shaded_renderer.render(gt_stl_path)
        blueprint_save_path.write_bytes(views.iso)
    return blueprint_save_path


def stl_to_step(stl_path: str, step_path: Path) -> bool:
    """trimesh で STL → CadQuery → STEP 出力（GT の STEP が無い場合の補完）。"""
    try:
        import cadquery as cq
        # CadQuery には直接 STL → STEP 変換はないが、trimesh で形状を保ってから
        # OCC.cadquery で STEP 出力は trimesh→occt 経由で可能。
        # しかしこの変換は信頼性が低いので、まず CadQuery 自身で再エクスポート試行。
        # ここでは「gen STL を再 exportcq」する用途では使わず、Skip の signal にする。
        return False
    except Exception:
        return False


def build_in_memory_setup():
    """全 use case + repo + corrector のセット（main.py の DI 簡略版）。"""
    from app.infrastructure.persistence.in_memory_blueprint_repository import (
        InMemoryBlueprintRepository,
    )
    from app.infrastructure.persistence.in_memory_cad_model_repository import (
        InMemoryCADModelRepository,
    )
    from app.infrastructure.cad.cadquery_executor import CadQueryExecutor
    from app.infrastructure.rendering.trimesh_pyrender_renderer import TrimeshPyrenderRenderer
    from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer
    from app.infrastructure.verification.anthropic_model_verifier import AnthropicModelVerifier
    from app.infrastructure.vlm.anthropic.anthropic_script_generator import (
        AnthropicScriptGenerator,
    )
    from app.infrastructure.correction_tools.anthropic_tool_corrector import (
        AnthropicToolBasedCorrector,
    )
    from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase
    from app.usecase.verify_and_correct_usecase import VerifyAndCorrectUseCase

    api_key = os.environ["ANTHROPIC_API_KEY"]
    blueprint_repo = InMemoryBlueprintRepository()
    cad_model_repo = InMemoryCADModelRepository()
    # /tmp/cad_output は本番と分離（既存 main.py の executor が消すため）
    cad_output_dir = "/tmp/cadprompt_loop_output"
    os.makedirs(cad_output_dir, exist_ok=True)
    cad_executor = CadQueryExecutor(output_dir=cad_output_dir)

    shaded_renderer = TrimeshPyrenderRenderer()
    line_renderer = CadQuerySvgRenderer()
    verifier = AnthropicModelVerifier(api_key=api_key, model="claude-opus-4-7")
    script_gen = AnthropicScriptGenerator(api_key=api_key, model="claude-opus-4-7")
    tool_corrector = AnthropicToolBasedCorrector(api_key=api_key, model="claude-opus-4-7")

    verify_uc = VerifyCadModelUseCase(
        blueprint_repo, cad_model_repo, shaded_renderer, line_renderer,
        verifier, cad_output_dir=cad_output_dir,
    )
    vandc_uc = VerifyAndCorrectUseCase(
        cad_model_repo, script_gen, cad_executor, verify_uc,
        tool_based_corrector=tool_corrector,
    )
    return {
        "blueprint_repo": blueprint_repo,
        "cad_model_repo": cad_model_repo,
        "cad_executor": cad_executor,
        "script_gen": script_gen,
        "verify_uc": verify_uc,
        "vandc_uc": vandc_uc,
        "cad_output_dir": cad_output_dir,
    }


def run_one_with_loop(entry: dict, setup: dict, output_dir: Path,
                     use_measurements: bool = False,
                     max_iter: int = 3,
                     use_tool_based: bool = True,
                     early_stop: int = 1) -> dict:
    """1 エントリを Verifier-Corrector ループで処理。"""
    from app.domain.entities.blueprint import Blueprint
    from app.domain.entities.cad_model import CADModel, GenerationStatus
    from app.domain.value_objects.cad_script import CadScript
    from app.domain.value_objects.design_step import DesignStep
    from app.domain.value_objects.loop_config import LoopConfig

    obj_id = entry["id"]
    prompt = entry["prompt_with_measurements"] if use_measurements else entry["prompt_abstract"]

    rec: dict = {
        "id": obj_id,
        "prompt_type": "with_measurements" if use_measurements else "abstract",
        "prompt": prompt,
    }

    started = time.time()

    # 1. blueprint 画像を準備（GT STL → iso line drawing）
    bp_path = output_dir / f"{obj_id}_blueprint.png"
    try:
        render_gt_blueprint(entry["gt_stl"], None, bp_path)
    except Exception as e:
        rec["error"] = f"blueprint render failed: {type(e).__name__}: {e}"
        rec["elapsed"] = time.time() - started
        return rec

    blueprint_id = f"bp-{obj_id}"
    bp = Blueprint(id=blueprint_id, file_path=str(bp_path),
                   file_name=bp_path.name, content_type="image/png")
    setup["blueprint_repo"].save(bp)

    # 2. 初期 CadQuery 生成
    try:
        steps = [DesignStep(step_number=1, instruction=prompt)]
        cad_script = setup["script_gen"].generate(steps, clarifications=[])
        rec["initial_script"] = cad_script.content
    except Exception as e:
        rec["error"] = f"generate failed: {type(e).__name__}: {e}"
        rec["elapsed"] = time.time() - started
        return rec

    # 3. 実行
    try:
        exec_result = setup["cad_executor"].execute(cad_script)
        rec["initial_compile_ok"] = True
    except Exception as e:
        rec["initial_compile_ok"] = False
        rec["error"] = f"initial execute failed: {type(e).__name__}: {e}"
        rec["elapsed"] = time.time() - started
        return rec

    # 4. CADModel 構築
    model_id = str(uuid.uuid4())
    cad_model = CADModel(
        id=model_id,
        blueprint_id=blueprint_id,
        status=GenerationStatus.SUCCESS,
        stl_path=exec_result.stl_filename,
        step_path=exec_result.step_filename,
        cad_script=cad_script,
        parameters=exec_result.parameters,
    )
    setup["cad_model_repo"].save(cad_model)

    # 4.5. 初期 STL のメトリクス（loop 適用前）
    init_stl_abs = os.path.join(setup["cad_output_dir"], exec_result.stl_filename)
    try:
        init_metrics = compute_metrics(entry["gt_stl"], init_stl_abs)
        rec["init_chamfer"] = init_metrics["chamfer"]
        rec["init_iou"] = init_metrics["iou"]
        rec["init_iogt"] = init_metrics["iogt"]
    except Exception as e:
        rec["init_metrics_error"] = f"{type(e).__name__}: {e}"

    # 5. Verifier-Corrector ループ
    try:
        cfg = LoopConfig(
            max_iterations=max_iter,
            single_fix_per_iteration=True,
            use_tool_based_correction=use_tool_based,
            early_stop_no_improve_k=early_stop,
        )
        cad_model_after, last_result, outcome, best_iter = setup["vandc_uc"].execute(
            model_id, cfg,
        )
        rec["loop_outcome"] = outcome
        rec["best_iter"] = best_iter
        rec["iter_count"] = len(cad_model_after.verification_history)
        rec["final_critical"] = last_result.critical_count()
        rec["final_major"] = last_result.major_count()
        rec["final_minor"] = last_result.minor_count()
    except Exception as e:
        rec["loop_error"] = f"{type(e).__name__}: {e}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # 6. 最終 STL のメトリクス（loop 後）
    final_stl_abs = os.path.join(setup["cad_output_dir"], cad_model_after.stl_path)
    try:
        final_metrics = compute_metrics(entry["gt_stl"], final_stl_abs)
        rec["final_chamfer"] = final_metrics["chamfer"]
        rec["final_iou"] = final_metrics["iou"]
        rec["final_iogt"] = final_metrics["iogt"]
        rec["chamfer_delta"] = (
            rec.get("init_chamfer", 0) - rec["final_chamfer"]
            if "init_chamfer" in rec else None
        )
        rec["iou_delta"] = (
            rec["final_iou"] - rec.get("init_iou", 0)
            if "init_iou" in rec else None
        )
    except Exception as e:
        rec["final_metrics_error"] = f"{type(e).__name__}: {e}"

    rec["elapsed"] = round(time.time() - started, 2)
    return rec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=20)
    parser.add_argument("--with-measurements", action="store_true")
    parser.add_argument("--max-iter", type=int, default=3)
    parser.add_argument("--no-tool-based", action="store_true",
                        help="Use text-based Corrector instead of Tool Use")
    parser.add_argument("--early-stop", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    label_parts = ["loop", "abstract" if not args.with_measurements else "wmeas",
                   "tool" if not args.no_tool_based else "text",
                   f"n{args.num_samples}", f"iter{args.max_iter}"]
    out_subdir = OUTPUT_DIR / "_".join(label_parts)
    out_subdir.mkdir(parents=True, exist_ok=True)

    setup = build_in_memory_setup()

    all_entries = list_entries()
    import random
    rng = random.Random(args.seed)
    sampled = rng.sample(all_entries, min(args.num_samples, len(all_entries)))

    print(f"=== CADPrompt Verifier-Corrector loop benchmark "
          f"({'wmeas' if args.with_measurements else 'abstract'}, "
          f"N={len(sampled)}, max_iter={args.max_iter}, "
          f"tool_based={not args.no_tool_based}) ===\n")

    results: list[dict] = []
    for i, p in enumerate(sampled, 1):
        entry = load_entry(p)
        print(f"[{i}/{len(sampled)}] {entry['id']} ...", end="", flush=True)
        try:
            rec = run_one_with_loop(
                entry, setup, out_subdir,
                use_measurements=args.with_measurements,
                max_iter=args.max_iter,
                use_tool_based=not args.no_tool_based,
                early_stop=args.early_stop,
            )
        except Exception as e:
            print(f" FAIL outer: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue
        results.append(rec)

        if "error" in rec:
            print(f" ERR ({rec['error'][:80]}) elapsed={rec['elapsed']:.1f}s")
        elif "loop_error" in rec:
            print(f" LOOP_ERR ({rec['loop_error'][:80]}) elapsed={rec['elapsed']:.1f}s")
        else:
            init_c = rec.get("init_chamfer")
            final_c = rec.get("final_chamfer")
            outcome = rec.get("loop_outcome", "?")
            print(
                f" {outcome} init_c={init_c:.3f} → final_c={final_c:.3f} "
                f"(Δ={rec.get('chamfer_delta', 0):+.3f}) "
                f"iter={rec.get('iter_count', 0)} elapsed={rec['elapsed']:.1f}s"
            )

    if not results:
        print("\n[!] no results")
        return 1

    # 集計
    n = len(results)
    init_chamfers = [r["init_chamfer"] for r in results if isinstance(r.get("init_chamfer"), float)]
    final_chamfers = [r["final_chamfer"] for r in results if isinstance(r.get("final_chamfer"), float)]
    deltas = [r["chamfer_delta"] for r in results if isinstance(r.get("chamfer_delta"), float)]
    init_ious = [r["init_iou"] for r in results if isinstance(r.get("init_iou"), float) and not np.isnan(r["init_iou"])]
    final_ious = [r["final_iou"] for r in results if isinstance(r.get("final_iou"), float) and not np.isnan(r["final_iou"])]
    outcomes: dict[str, int] = {}
    for r in results:
        oc = r.get("loop_outcome", "error")
        outcomes[oc] = outcomes.get(oc, 0) + 1

    print("\n" + "=" * 70)
    print(f"=== Summary: CADPrompt + Verifier-Corrector loop (N={n}) ===")
    print(f"\n--- 形状品質（生成直後 → ループ後）---")
    if init_chamfers and final_chamfers:
        print(f"chamfer mean:   {statistics.mean(init_chamfers):.4f} → "
              f"{statistics.mean(final_chamfers):.4f}  "
              f"(改善 {statistics.mean(deltas):+.4f}, "
              f"中央値 {statistics.median(deltas):+.4f})")
    if init_ious and final_ious:
        print(f"IoU mean:       {statistics.mean(init_ious):.3f} → "
              f"{statistics.mean(final_ious):.3f}  "
              f"(差 {statistics.mean(final_ious)-statistics.mean(init_ious):+.3f})")
    print(f"\n--- ループの結末 ---")
    for k, v in sorted(outcomes.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({100*v/n:.0f}%)")

    n_improved = sum(1 for d in deltas if d > 0.001)
    n_degraded = sum(1 for d in deltas if d < -0.001)
    n_same = len(deltas) - n_improved - n_degraded
    print(f"\n--- chamfer 変化（ループの実用効果）---")
    print(f"  改善:    {n_improved}/{len(deltas)} ({100*n_improved/len(deltas):.0f}%)")
    print(f"  悪化:    {n_degraded}/{len(deltas)} ({100*n_degraded/len(deltas):.0f}%)")
    print(f"  ほぼ同等: {n_same}/{len(deltas)} ({100*n_same/len(deltas):.0f}%)")

    out_path = out_subdir / "results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
