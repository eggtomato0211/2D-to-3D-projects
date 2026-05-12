"""CADPrompt ベンチマークで本プロジェクトの script_generator を評価。

CADCodeVerify 論文の指標との比較を目的とする:
- Compile rate（実行が通る割合）
- Chamfer distance（点群間距離）
- Hausdorff distance
- IoGT (Intersection over Ground Truth)、簡易版

CADCodeVerify 報告値（参考）:
- GPT-4:        compile 96.5%, refinement で point cloud distance -7.30%
- Gemini 1.5:   compile 85.0%
- CodeLlama:    compile 73.5%
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import trimesh

EXPERIMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = EXPERIMENT_DIR / "data"
OUTPUT_DIR = EXPERIMENT_DIR / "output"


# ------------------------------------------------------------------
# サンプリング
# ------------------------------------------------------------------
def list_entries() -> list[Path]:
    # 隠しファイル（.DS_Store 等）と非ディレクトリを除外
    return sorted(p for p in DATA_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


def load_entry(path: Path) -> dict:
    obj_id = path.name
    return {
        "id": obj_id,
        "path": path,
        "prompt_abstract": (path / "Natural_Language_Descriptions_Prompt.txt").read_text(encoding="utf-8").strip(),
        "prompt_with_measurements": (path / "Natural_Language_Descriptions_Prompt_with_specific_measurements.txt").read_text(encoding="utf-8").strip(),
        "expert_code": (path / "Python_Code.py").read_text(encoding="utf-8"),
        "gt_stl": str(path / "Ground_Truth.stl"),
    }


# ------------------------------------------------------------------
# 生成
# ------------------------------------------------------------------
def generate_script(prompt_text: str, sg) -> tuple[str, str | None]:
    """script_generator で CadQuery スクリプトを生成。

    Step 1（analyzer）はスキップして、自然言語プロンプトを直接 generate に渡す。
    実装上、generate は DesignStep のリストを取るので 1-step として包む。
    """
    from app.domain.value_objects.design_step import DesignStep
    steps = [DesignStep(step_number=1, instruction=prompt_text)]
    cad_script = sg.generate(steps, clarifications=[])
    return cad_script.content, None


# ------------------------------------------------------------------
# 実行 + メトリクス
# ------------------------------------------------------------------
def execute_script(script_content: str, out_stl_path: Path) -> tuple[bool, str | None]:
    """CadQuery スクリプトを実行し、STL を出力。"""
    namespace: dict = {}
    try:
        exec(script_content, namespace)
        result = namespace.get("result") or namespace.get("part")
        if result is None:
            return False, "result/part variable not found"
        import cadquery as cq
        cq.exporters.export(result, str(out_stl_path))
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def compute_metrics(gt_stl: str, gen_stl: str,
                    num_points: int = 4096, voxel_pitch: float = 0.02) -> dict:
    """点群＋ボクセルベースのメトリクス。

    - Chamfer / Hausdorff: 点群 NN 距離（watertight 不要）
    - Volume IoU: 正規化メッシュをボクセル化して計算（IoGT のバグ回避）

    両メッシュは bbox 中心揃え + 最大辺=1 にスケール正規化してから比較する。
    """
    gt_mesh = trimesh.load(gt_stl, force="mesh")
    gen_mesh = trimesh.load(gen_stl, force="mesh")

    def _normalize(m: trimesh.Trimesh) -> trimesh.Trimesh:
        m2 = m.copy()
        m2.apply_translation(-m2.bounds.mean(axis=0))
        scale = max(m2.extents)
        if scale > 1e-9:
            m2.apply_scale(1.0 / scale)
        return m2

    gt_n = _normalize(gt_mesh)
    gen_n = _normalize(gen_mesh)

    gt_pts = gt_n.sample(num_points)
    gen_pts = gen_n.sample(num_points)

    # Chamfer distance: 双方向 NN 距離平均
    from scipy.spatial import cKDTree
    tree_gt = cKDTree(gt_pts)
    tree_gen = cKDTree(gen_pts)
    d1, _ = tree_gt.query(gen_pts)
    d2, _ = tree_gen.query(gt_pts)
    chamfer = float(np.mean(d1) + np.mean(d2))

    # Hausdorff
    hausdorff = float(max(d1.max(), d2.max()))

    # Volume IoU: 正規化空間 [-0.5, 0.5]^3 をボクセル化して計算
    iou = float("nan")
    iogt = float("nan")
    try:
        gt_vox = gt_n.voxelized(pitch=voxel_pitch).fill()
        gen_vox = gen_n.voxelized(pitch=voxel_pitch).fill()
        # 共通 grid に揃える
        gt_pts_idx = set(map(tuple, gt_vox.points.astype(np.int32).tolist()))
        gen_pts_idx = set(map(tuple, gen_vox.points.astype(np.int32).tolist()))
        # ↑ points は世界座標なので、index 化のため pitch でスケールしておく
        gt_idx = set(tuple(np.round(p / voxel_pitch).astype(int)) for p in gt_vox.points)
        gen_idx = set(tuple(np.round(p / voxel_pitch).astype(int)) for p in gen_vox.points)
        if gt_idx and gen_idx:
            inter = len(gt_idx & gen_idx)
            union = len(gt_idx | gen_idx)
            iou = float(inter / union) if union else 0.0
            iogt = float(inter / len(gt_idx)) if gt_idx else 0.0
    except Exception as e:
        iou_err = f"{type(e).__name__}: {e}"
        return {
            "chamfer": chamfer,
            "hausdorff": hausdorff,
            "iou": iou,
            "iogt": iogt,
            "gt_volume": float(gt_n.volume) if gt_n.is_volume else None,
            "gen_volume": float(gen_n.volume) if gen_n.is_volume else None,
            "iou_error": iou_err,
        }

    return {
        "chamfer": chamfer,
        "hausdorff": hausdorff,
        "iou": iou,
        "iogt": iogt,
        "gt_volume": float(gt_n.volume) if gt_n.is_volume else None,
        "gen_volume": float(gen_n.volume) if gen_n.is_volume else None,
    }


# ------------------------------------------------------------------
# Runner
# ------------------------------------------------------------------
def run_one(entry: dict, sg, output_dir: Path,
            use_measurements: bool = False) -> dict:
    obj_id = entry["id"]
    prompt = entry["prompt_with_measurements"] if use_measurements else entry["prompt_abstract"]
    rec: dict = {
        "id": obj_id,
        "prompt_type": "with_measurements" if use_measurements else "abstract",
        "prompt": prompt,
    }

    started = time.time()
    try:
        script, gen_err = generate_script(prompt, sg)
        rec["generated_script"] = script
        rec["gen_error"] = gen_err
    except Exception as e:
        rec["generated_script"] = None
        rec["gen_error"] = f"{type(e).__name__}: {e}"
        rec["compile_ok"] = False
        rec["elapsed"] = time.time() - started
        return rec

    out_stl = output_dir / f"{obj_id}.stl"
    compile_ok, exec_err = execute_script(script, out_stl)
    rec["compile_ok"] = compile_ok
    rec["exec_error"] = exec_err

    if compile_ok:
        try:
            metrics = compute_metrics(entry["gt_stl"], str(out_stl))
            rec.update(metrics)
        except Exception as e:
            rec["metrics_error"] = f"{type(e).__name__}: {e}"
    rec["elapsed"] = round(time.time() - started, 2)
    return rec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=20)
    parser.add_argument("--with-measurements", action="store_true",
                        help="寸法付きプロンプトで実行 (default: abstract)")
    parser.add_argument("--seed", type=int, default=42, help="サンプルランダム性")
    parser.add_argument("--ids", help="特定 ID リスト（カンマ区切り）", default=None)
    parser.add_argument("--resume", action="store_true",
                        help="既存の results_partial.json を読み込んで処理済み ID をスキップ")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_label = "with_measurements" if args.with_measurements else "abstract"
    out_subdir = OUTPUT_DIR / f"run_{run_label}_n{args.num_samples}"
    out_subdir.mkdir(parents=True, exist_ok=True)

    # Script generator のセットアップ（main.py の DI を借用せず最小構成）
    sys.path.insert(0, "/app")
    from app.infrastructure.vlm.anthropic.anthropic_script_generator import (
        AnthropicScriptGenerator,
    )
    import os
    sg = AnthropicScriptGenerator(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-opus-4-7",
    )
    # 長時間ハング対策: Anthropic SDK にリクエストタイムアウトを設定
    sg.client = sg.client.with_options(timeout=120.0, max_retries=2)

    # サンプリング
    all_entries = list_entries()
    if args.ids:
        wanted = set(args.ids.split(","))
        entries = [p for p in all_entries if p.name in wanted]
    else:
        import random
        rng = random.Random(args.seed)
        entries = rng.sample(all_entries, min(args.num_samples, len(all_entries)))

    print(f"=== CADPrompt benchmark ({run_label}, N={len(entries)}) ===\n")

    # --resume: 既存の results_partial.json を読み込み、処理済み ID を skip
    intermediate_path = out_subdir / "results_partial.json"
    results: list[dict] = []
    done_ids: set[str] = set()
    if args.resume and intermediate_path.exists():
        results = json.loads(intermediate_path.read_text(encoding="utf-8"))
        done_ids = {r["id"] for r in results}
        print(f"[resume] loaded {len(results)} prior results, skipping...\n")

    for i, p in enumerate(entries, 1):
        if p.name in done_ids:
            continue
        entry = load_entry(p)
        print(f"[{i}/{len(entries)}] {entry['id']} ...", end="", flush=True)
        try:
            rec = run_one(entry, sg, out_subdir, args.with_measurements)
        except Exception as e:
            print(f" FAIL: {type(e).__name__}: {e}")
            traceback.print_exc()
            rec = {"id": entry["id"], "fatal_error": f"{type(e).__name__}: {e}"}
        results.append(rec)
        ok = "OK" if rec.get("compile_ok") else "FAIL"
        cd = rec.get("chamfer")
        cd_str = f"chamfer={cd:.4f}" if isinstance(cd, float) else "chamfer=N/A"
        print(f" {ok} {cd_str} ({rec.get('elapsed', 'n/a')}s)", flush=True)
        # 5件ごとに中間保存（途中で落ちても結果が残る）
        if i % 5 == 0:
            intermediate_path.write_text(
                json.dumps(results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # 結果集計
    n = len(results)
    if n == 0:
        print("\n[!] no results")
        return 1

    compile_ok_count = sum(1 for r in results if r.get("compile_ok"))
    chamfers = [r["chamfer"] for r in results if isinstance(r.get("chamfer"), float)]
    hausdorffs = [r["hausdorff"] for r in results if isinstance(r.get("hausdorff"), float)]
    ious = [r["iou"] for r in results if isinstance(r.get("iou"), float) and not np.isnan(r["iou"])]
    iogts = [r["iogt"] for r in results if isinstance(r.get("iogt"), float) and not np.isnan(r["iogt"])]

    print("\n" + "=" * 60)
    print(f"=== Summary: CADPrompt {run_label} (N={n}) ===")
    print(f"compile rate:        {100*compile_ok_count/n:.1f}% ({compile_ok_count}/{n})")
    if chamfers:
        print(f"chamfer (mean):      {statistics.mean(chamfers):.4f}")
        print(f"chamfer (median):    {statistics.median(chamfers):.4f}")
        print(f"chamfer (stdev):     {statistics.stdev(chamfers) if len(chamfers)>1 else 0:.4f}")
    if hausdorffs:
        print(f"hausdorff (mean):    {statistics.mean(hausdorffs):.4f}")
    if ious:
        print(f"IoU (mean):          {statistics.mean(ious):.3f}")
        print(f"IoU (median):        {statistics.median(ious):.3f}")
    if iogts:
        print(f"IoGT (mean):         {statistics.mean(iogts):.3f}")
    print()
    print(f"参考: CADCodeVerify 論文（GPT-4）  compile rate 96.5%")
    print(f"      CADCodeVerify (Gemini 1.5)   compile rate 85.0%")
    print(f"      CADCodeVerify (CodeLlama)   compile rate 73.5%")

    out_path = out_subdir / "results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
