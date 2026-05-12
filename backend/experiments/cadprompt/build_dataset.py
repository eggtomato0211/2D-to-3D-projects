"""CADPrompt サンプルから 2D 図面 + 3D モデルのペアを束ねたデータセットを構築する。

出力フォルダ構造:
    <output_dir>/
      manifest.json                # 全エントリの索引
      <obj_id>/
        drawing.png                # 2D 図面（線画 4 視点 + bbox 寸法 + Ø ラベル + タイトルブロック）
        model.stl                  # 3D モデル（STL）
        model.step                 # 3D モデル（STEP）
        metadata.json              # bbox、フィーチャサマリ、元 CADPrompt のプロンプト
        expert_code.py             # 元 CADPrompt の Python_Code.py

使い方:
    python -m experiments.cadprompt.build_dataset -n 100
    python -m experiments.cadprompt.build_dataset --all
    python -m experiments.cadprompt.build_dataset --output-name my_dataset_v1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, "/app")

import cadquery as cq

from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer

# 既存の描画ヘルパーを再利用
from experiments.cadprompt.render_line_demo import (
    compose_drawing_sheet,
    extract_features,
    summarize_features,
)

EXPERIMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = EXPERIMENT_DIR / "data"


def _list_ids() -> list[str]:
    return sorted(p.name for p in DATA_DIR.iterdir()
                  if p.is_dir() and not p.name.startswith("."))


def _load_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def build_one(obj_id: str, out_root: Path) -> dict:
    """1 サンプルを生成し、メタ情報を返す。"""
    src_dir = DATA_DIR / obj_id
    if not src_dir.is_dir():
        return {"id": obj_id, "ok": False, "error": "source dir not found"}

    code_path = src_dir / "Python_Code.py"
    code = code_path.read_text(encoding="utf-8")

    out_dir = out_root / obj_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Python_Code.py を実行（最後に Ground_Truth.stl を export するので、cwd を一時的に
    # out_dir に変更する）
    namespace: dict = {}
    cwd = os.getcwd()
    os.chdir(str(out_dir))
    try:
        exec(code, namespace)
    finally:
        os.chdir(cwd)

    part = namespace.get("part") or namespace.get("result")
    if part is None:
        return {"id": obj_id, "ok": False, "error": "no `part` or `result` found"}

    # bbox 最大辺 = 100mm に正規化（CADPrompt は極小モデルが多い）
    solid = part.val() if hasattr(part, "val") else part
    bbox = solid.BoundingBox()
    max_extent = max(bbox.xlen, bbox.ylen, bbox.zlen)
    target = 100.0
    if max_extent > 1e-9 and abs(max_extent - target) > 1e-6:
        scale = target / max_extent
        try:
            scaled_part = part.translate((-bbox.center.x, -bbox.center.y, -bbox.center.z))
        except Exception:
            scaled_part = part
        s = scaled_part.val() if hasattr(scaled_part, "val") else scaled_part
        scaled_solid = s.scale(scale)
        part = cq.Workplane().add(scaled_solid)

    # スケール後の bbox を取得
    scaled_solid = part.val() if hasattr(part, "val") else part
    sb = scaled_solid.BoundingBox()
    bbox_mm = (sb.xlen, sb.ylen, sb.zlen)

    # 3D モデル出力
    stl_path = out_dir / "model.stl"
    step_path = out_dir / "model.step"
    cq.exporters.export(part, str(stl_path))
    cq.exporters.export(part, str(step_path))

    # 元の Ground_Truth.stl は削除（重複を避ける）
    leftover = out_dir / "Ground_Truth.stl"
    if leftover.exists():
        try:
            leftover.unlink()
        except Exception:
            pass

    # フィーチャ抽出
    raw_features = extract_features(scaled_solid)
    features_summary = summarize_features(raw_features)

    # 4 視点 + 1 枚図面の生成
    renderer = CadQuerySvgRenderer()
    views = renderer.render(str(step_path))
    sheet_png = compose_drawing_sheet(
        obj_id=obj_id,
        views_top=views.top,
        views_front=views.front,
        views_side=views.side,
        views_iso=views.iso,
        bbox_mm=bbox_mm,
        features_summary=features_summary,
        cylinders=raw_features["cylinders"],
        title="DeepCAD / CADPrompt sample",
    )
    drawing_path = out_dir / "drawing.png"
    drawing_path.write_bytes(sheet_png)

    # 元 CADPrompt のメタ
    prompt_abstract = _load_text(src_dir / "Natural_Language_Descriptions_Prompt.txt")
    prompt_with_meas = _load_text(src_dir / "Natural_Language_Descriptions_Prompt_with_specific_measurements.txt")

    # expert_code を保存
    (out_dir / "expert_code.py").write_text(code, encoding="utf-8")

    metadata = {
        "id": obj_id,
        "bbox_mm": {"x": bbox_mm[0], "y": bbox_mm[1], "z": bbox_mm[2]},
        "scale_normalized_to_mm": target,
        "features": features_summary,
        "cylinders_count": len(raw_features["cylinders"]),
        "tori_count": len(raw_features["tori"]),
        "cones_count": len(raw_features["cones"]),
        "prompt_abstract": (prompt_abstract or "").strip() or None,
        "prompt_with_measurements": (prompt_with_meas or "").strip() or None,
        "files": {
            "drawing": "drawing.png",
            "stl": "model.stl",
            "step": "model.step",
            "expert_code": "expert_code.py",
        },
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {"id": obj_id, "ok": True, "path": str(out_dir)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=20,
                        help="生成するサンプル数（--all 指定時は無視）")
    parser.add_argument("--all", action="store_true",
                        help="全 200 サンプルを処理")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-name", default="dataset_v1",
                        help="出力フォルダ名（experiments/cadprompt/<name>/）")
    parser.add_argument("--ids", default=None,
                        help="特定 ID リスト（カンマ区切り）。指定時は -n / --all 無視")
    args = parser.parse_args()

    out_root = EXPERIMENT_DIR / args.output_name
    out_root.mkdir(parents=True, exist_ok=True)

    all_ids = _list_ids()

    if args.ids:
        wanted = [s.strip() for s in args.ids.split(",") if s.strip()]
        ids = [i for i in wanted if i in set(all_ids)]
    elif args.all:
        ids = all_ids
    else:
        import random
        rng = random.Random(args.seed)
        ids = rng.sample(all_ids, min(args.num_samples, len(all_ids)))
        ids.sort()

    print(f"=== build_dataset → {out_root} (N={len(ids)}) ===\n")
    started = time.time()
    manifest_entries: list[dict] = []
    fail_count = 0
    for i, obj_id in enumerate(ids, 1):
        t0 = time.time()
        try:
            r = build_one(obj_id, out_root)
        except Exception as e:
            print(f"[{i}/{len(ids)}] {obj_id} FAIL: {type(e).__name__}: {e}")
            traceback.print_exc()
            fail_count += 1
            continue
        elapsed = round(time.time() - t0, 2)
        if r["ok"]:
            manifest_entries.append({"id": obj_id, "path": obj_id})
            print(f"[{i}/{len(ids)}] {obj_id} OK ({elapsed}s)")
        else:
            print(f"[{i}/{len(ids)}] {obj_id} FAIL: {r.get('error')}")
            fail_count += 1

    manifest = {
        "name": args.output_name,
        "source": "CADPrompt (DeepCAD subset)",
        "total": len(manifest_entries),
        "failed": fail_count,
        "scale_normalized_to_mm": 100.0,
        "entries": manifest_entries,
        "structure": {
            "drawing": "<id>/drawing.png — 2D 線画 4 視点 + 寸法 + Ø ラベル + タイトル",
            "stl":     "<id>/model.stl — 3D メッシュ（正規化済 mm）",
            "step":    "<id>/model.step — 3D 厳密形状（正規化済 mm）",
            "metadata":"<id>/metadata.json — bbox / features / プロンプト",
            "expert_code": "<id>/expert_code.py — 元 CadQuery 専門家コード",
        },
    }
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_time = round(time.time() - started, 1)
    print(f"\n[*] {len(manifest_entries)}/{len(ids)} entries built (failed={fail_count}) in {total_time}s")
    print(f"[*] manifest: {out_root / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
