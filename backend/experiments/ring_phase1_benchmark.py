"""Phase 1（VLM 言語化）強化の効果を RING 図面で計測する。

各サンプルでフルパイプライン（analyze → generate → execute → verify）を実行し、
以下を記録する:
- dimensions_table 件数
- feature_inventory 件数
- design step 数
- compile_ok
- verifier critical_count

N サンプルの分布で安定性も評価する（RING は LLM の確率的揺れが大きい）。
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

EXPERIMENT_DIR = Path(__file__).resolve().parent
RING_BLUEPRINT = EXPERIMENT_DIR / "vlm_eval" / "cases_b" / "ring" / "drawing.png"


def _build_components():
    sys.path.insert(0, "/app")
    from app.domain.entities.blueprint import Blueprint
    from app.domain.entities.cad_model import CADModel, GenerationStatus
    from app.infrastructure.cad.cadquery_executor import CadQueryExecutor
    from app.infrastructure.persistence.in_memory_blueprint_repository import (
        InMemoryBlueprintRepository,
    )
    from app.infrastructure.persistence.in_memory_cad_model_repository import (
        InMemoryCADModelRepository,
    )
    from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer
    from app.infrastructure.rendering.trimesh_pyrender_renderer import (
        TrimeshPyrenderRenderer,
    )
    from app.infrastructure.verification.anthropic_model_verifier import (
        AnthropicModelVerifier,
    )
    from app.infrastructure.vlm.anthropic.anthropic_blueprint_analyzer import (
        AnthropicBlueprintAnalyzer,
    )
    from app.infrastructure.vlm.anthropic.anthropic_script_generator import (
        AnthropicScriptGenerator,
    )
    from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase

    api_key = os.environ["ANTHROPIC_API_KEY"]
    model_id = "claude-opus-4-7"

    bp_repo = InMemoryBlueprintRepository()
    cm_repo = InMemoryCADModelRepository()

    analyzer = AnthropicBlueprintAnalyzer(api_key=api_key, model=model_id)
    sg = AnthropicScriptGenerator(api_key=api_key, model=model_id)
    sg.client = sg.client.with_options(timeout=120.0, max_retries=2)
    analyzer.client = analyzer.client.with_options(timeout=120.0, max_retries=2)

    executor = CadQueryExecutor(output_dir="/tmp/cad_output_ring_bench")

    verifier = AnthropicModelVerifier(api_key=api_key, model=model_id)
    shaded = TrimeshPyrenderRenderer()
    line = CadQuerySvgRenderer()
    verify_uc = VerifyCadModelUseCase(
        bp_repo, cm_repo, shaded, line, verifier,
        cad_output_dir="/tmp/cad_output_ring_bench",
    )

    return {
        "Blueprint": Blueprint,
        "CADModel": CADModel,
        "GenerationStatus": GenerationStatus,
        "bp_repo": bp_repo,
        "cm_repo": cm_repo,
        "analyzer": analyzer,
        "sg": sg,
        "executor": executor,
        "verify_uc": verify_uc,
    }


def run_one(comps: dict, blueprint_id: str, sample_idx: int) -> dict:
    Blueprint = comps["Blueprint"]
    CADModel = comps["CADModel"]
    GenerationStatus = comps["GenerationStatus"]
    bp_repo = comps["bp_repo"]
    cm_repo = comps["cm_repo"]
    analyzer = comps["analyzer"]
    sg = comps["sg"]
    executor = comps["executor"]
    verify_uc = comps["verify_uc"]

    rec: dict = {"sample": sample_idx}
    started = time.time()
    bp = bp_repo.get_by_id(blueprint_id)

    # Phase 1: analyze
    try:
        steps, clarifications = analyzer.analyze(bp)
        rec["steps_count"] = len(steps)
        rec["clarifications_count"] = len(clarifications)
        # 構造化抽出が steps[0] に埋め込まれているかを検出
        first_instr = steps[0].instruction if steps else ""
        has_dim_table = "dimensions_table" in first_instr or "寸法表" in first_instr
        rec["has_dimensions_table"] = has_dim_table
        # 寸法行数を雑に推定（"| symbol |" 行 + データ行）
        dim_lines = [ln for ln in first_instr.splitlines() if ln.startswith("| ") and "---" not in ln]
        rec["dimensions_rows"] = max(0, len(dim_lines) - 1)  # ヘッダー除く
        feat_lines = [ln for ln in first_instr.splitlines() if ln.startswith("- **")]
        rec["features_count"] = len(feat_lines)
        rec["first_step_excerpt"] = first_instr[:400]
    except Exception as e:
        rec["analyze_error"] = f"{type(e).__name__}: {e}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # Phase 2 (Step 2): script generate
    try:
        cad_script = sg.generate(steps, clarifications)
        rec["script_chars"] = len(cad_script.content)
        rec["script_content"] = cad_script.content
    except Exception as e:
        rec["generate_error"] = f"{type(e).__name__}: {e}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # Phase 2 (Step 3): execute
    try:
        exec_result = executor.execute(cad_script)
        rec["compile_ok"] = True
        rec["stl_filename"] = exec_result.stl_filename
    except Exception as e:
        rec["compile_ok"] = False
        rec["execute_error"] = f"{type(e).__name__}: {e}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # CADModel を repo に保存 → verifier に渡せるようにする
    model_id = str(uuid.uuid4())
    cad_model = CADModel(
        id=model_id,
        blueprint_id=blueprint_id,
        status=GenerationStatus.SUCCESS,
        stl_path=exec_result.stl_filename,
        step_path=exec_result.step_filename,
        cad_script=cad_script,
    )
    cm_repo.save(cad_model)

    # Phase 2-α/γ: verify
    try:
        outcome = verify_uc.execute(model_id)
        result = outcome.result
        rec["is_valid"] = result.is_valid
        rec["critical_count"] = result.critical_count()
        rec["major_count"] = result.major_count()
        rec["minor_count"] = result.minor_count()
        rec["discrepancy_summary"] = [
            {"sev": d.severity, "feat": d.feature_type, "desc": d.description[:80]}
            for d in result.discrepancies
        ]
    except Exception as e:
        rec["verify_error"] = f"{type(e).__name__}: {e}"

    rec["elapsed"] = round(time.time() - started, 2)
    return rec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=5)
    parser.add_argument("--label", default="post_phase1",
                        help="出力ファイル識別子（pre/post など）")
    args = parser.parse_args()

    comps = _build_components()
    Blueprint = comps["Blueprint"]
    bp_repo = comps["bp_repo"]

    blueprint_id = str(uuid.uuid4())
    bp = Blueprint(
        id=blueprint_id,
        file_path=str(RING_BLUEPRINT),
        file_name="ring.png",
        content_type="image/png",
    )
    bp_repo.save(bp)

    print(f"=== RING Phase 1 benchmark ({args.label}, N={args.num_samples}) ===\n")
    out_dir = EXPERIMENT_DIR / "vlm_eval" / "ring_phase1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"results_{args.label}_n{args.num_samples}.json"
    partial_path = out_dir / f"results_{args.label}_n{args.num_samples}.partial.json"
    results: list[dict] = []
    for i in range(1, args.num_samples + 1):
        print(f"[{i}/{args.num_samples}] ...", end="", flush=True)
        try:
            rec = run_one(comps, blueprint_id, i)
        except Exception as e:
            print(f" FAIL: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue
        results.append(rec)
        cc = rec.get("critical_count")
        cc_str = f"crit={cc}" if cc is not None else "crit=N/A"
        ok = "OK" if rec.get("compile_ok") else "FAIL"
        dim = rec.get("dimensions_rows", 0)
        feat = rec.get("features_count", 0)
        print(f" {ok} dims={dim} feats={feat} {cc_str} ({rec['elapsed']}s)")
        # 各サンプル後に中間保存
        partial_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # サマリ
    n = len(results)
    if n == 0:
        print("\n[!] no results")
        return 1

    compile_count = sum(1 for r in results if r.get("compile_ok"))
    crits = [r["critical_count"] for r in results if isinstance(r.get("critical_count"), int)]
    dims = [r.get("dimensions_rows", 0) for r in results]
    feats = [r.get("features_count", 0) for r in results]
    has_dim = sum(1 for r in results if r.get("has_dimensions_table"))

    print("\n" + "=" * 60)
    print(f"=== Summary: RING ({args.label}, N={n}) ===")
    print(f"compile rate:      {100*compile_count/n:.1f}% ({compile_count}/{n})")
    print(f"has_dim_table:     {100*has_dim/n:.1f}% ({has_dim}/{n})")
    print(f"dim rows mean:     {statistics.mean(dims):.1f} (range [{min(dims)}, {max(dims)}])")
    print(f"features mean:     {statistics.mean(feats):.1f} (range [{min(feats)}, {max(feats)}])")
    if crits:
        print(f"critical count:    mean={statistics.mean(crits):.2f} median={statistics.median(crits):.1f} min={min(crits)} max={max(crits)}")
        zero_crits = sum(1 for c in crits if c == 0)
        print(f"converged (c=0):   {100*zero_crits/len(crits):.1f}% ({zero_crits}/{len(crits)})")

    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
