"""DeepCAD raw JSON から 2D 図面 + 3D モデルのペアを束ねたデータセットを構築する。

CADPrompt build_dataset.py と同じ出力フォルダ構造:
    <output_dir>/
      manifest.json
      <id>/
        drawing.png            # 2D 図面（線画 4 視点 + bbox 寸法 + Ø ラベル）
        model.stl              # 3D メッシュ
        model.step             # 3D 厳密形状
        metadata.json          # bbox / features / source path
        source.json            # 元 DeepCAD JSON（CADSequence）

使い方:
    docker compose run --rm backend python -m experiments.deepcad.build_dataset -n 100
    docker compose run --rm backend python -m experiments.deepcad.build_dataset -n 1000 --split train
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/experiments/deepcad")

import cadquery as cq

from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer
from cadlib_ocp.extrude import CADSequence
from cadlib_ocp.visualize import create_CAD

from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.StlAPI import StlAPI_Writer
from OCP.BRepCheck import BRepCheck_Analyzer

from experiments.cadprompt.render_line_demo import (
    compose_drawing_sheet,
    extract_features,
    summarize_features,
)

EXPERIMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = EXPERIMENT_DIR / "data" / "cad_json"
SPLIT_FILE = EXPERIMENT_DIR / "data" / "train_val_test_split.json"


def _write_step(shape, path: Path) -> None:
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    status = writer.Write(str(path))
    if status != IFSelect_RetDone:
        raise RuntimeError(f"STEP write failed: status={status}")


def _write_stl(shape, path: Path) -> None:
    writer = StlAPI_Writer()
    writer.Write(shape, str(path))


def _list_json_paths(split: str | None = None, sample: int | None = None,
                     seed: int = 42) -> list[Path]:
    """JSON ファイルパスを列挙。split 指定時は train_val_test_split.json から抽出。"""
    if split is not None and SPLIT_FILE.exists():
        with open(SPLIT_FILE) as f:
            split_data = json.load(f)
        ids = split_data.get(split, [])
        # split 内の id は "0071/00717314" 形式
        paths = [DATA_DIR / f"{s}.json" for s in ids]
        paths = [p for p in paths if p.exists()]
    else:
        paths = sorted(DATA_DIR.rglob("*.json"))

    if sample is not None and sample < len(paths):
        rng = random.Random(seed)
        paths = sorted(rng.sample(paths, sample))
    return paths


def build_one(json_path: Path, out_root: Path) -> dict:
    """1 JSON を受け取り、データセットエントリを生成する。"""
    obj_id = json_path.stem
    out_dir = out_root / obj_id

    rec: dict = {"id": obj_id, "source": str(json_path.relative_to(DATA_DIR))}

    # JSON → CADSequence → TopoDS_Shape
    with open(json_path) as f:
        data = json.load(f)
    cad_seq = CADSequence.from_dict(data)
    cad_seq.normalize()
    shape = create_CAD(cad_seq)

    # 形状の妥当性チェック
    analyzer = BRepCheck_Analyzer(shape)
    if not analyzer.IsValid():
        rec["ok"] = False
        rec["error"] = "BRep invalid"
        return rec

    out_dir.mkdir(parents=True, exist_ok=True)

    # STEP / STL を一旦書き出し
    raw_step = out_dir / "_raw.step"
    _write_step(shape, raw_step)

    # CadQuery で読み直して bbox 正規化（max edge=100mm）
    imported = cq.importers.importStep(str(raw_step))
    solid = imported.val()
    bbox = solid.BoundingBox()
    max_extent = max(bbox.xlen, bbox.ylen, bbox.zlen)
    target = 100.0
    if max_extent < 1e-9:
        rec["ok"] = False
        rec["error"] = "degenerate bbox"
        try:
            shutil.rmtree(out_dir)
        except Exception:
            pass
        return rec

    scale = target / max_extent
    centered = imported.translate((-bbox.center.x, -bbox.center.y, -bbox.center.z))
    scaled_solid = centered.val().scale(scale)
    part = cq.Workplane().add(scaled_solid)

    sb = scaled_solid.BoundingBox()
    bbox_mm = (sb.xlen, sb.ylen, sb.zlen)

    # 正規化済 STEP/STL を最終配置
    step_path = out_dir / "model.step"
    stl_path = out_dir / "model.stl"
    cq.exporters.export(part, str(step_path))
    cq.exporters.export(part, str(stl_path))
    raw_step.unlink(missing_ok=True)

    # 特徴抽出
    raw_features = extract_features(scaled_solid)
    features_summary = summarize_features(raw_features)

    # 4 視点描画 + 1 枚図面合成
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
        title="DeepCAD raw",
    )
    (out_dir / "drawing.png").write_bytes(sheet_png)

    # 元 JSON も保存（再現性のため）
    (out_dir / "source.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )

    metadata = {
        "id": obj_id,
        "source_json": rec["source"],
        "bbox_mm": {"x": bbox_mm[0], "y": bbox_mm[1], "z": bbox_mm[2]},
        "scale_normalized_to_mm": target,
        "extrude_ops": len(cad_seq.seq),
        "features": features_summary,
        "cylinders_count": len(raw_features["cylinders"]),
        "tori_count": len(raw_features["tori"]),
        "cones_count": len(raw_features["cones"]),
        "files": {
            "drawing": "drawing.png",
            "stl": "model.stl",
            "step": "model.step",
            "source_json": "source.json",
        },
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rec["ok"] = True
    rec["path"] = str(out_dir)
    return rec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=100,
                        help="生成するサンプル数")
    parser.add_argument("--split", choices=["train", "validation", "test"], default=None,
                        help="DeepCAD 公式 split から選ぶ（未指定は全 JSON から）")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-name", default="dataset_v1",
                        help="出力フォルダ名（experiments/deepcad/<name>/）")
    args = parser.parse_args()

    out_root = EXPERIMENT_DIR / args.output_name
    out_root.mkdir(parents=True, exist_ok=True)
    partial_path = out_root / "manifest.partial.json"

    paths = _list_json_paths(split=args.split, sample=args.num_samples, seed=args.seed)
    print(f"=== build_deepcad_dataset → {out_root} (N={len(paths)}, split={args.split}) ===\n")

    started = time.time()
    manifest_entries: list[dict] = []
    fail_count = 0
    for i, p in enumerate(paths, 1):
        t0 = time.time()
        try:
            r = build_one(p, out_root)
        except Exception as e:
            print(f"[{i}/{len(paths)}] {p.stem} FAIL: {type(e).__name__}: {str(e)[:100]}")
            fail_count += 1
            continue
        elapsed = round(time.time() - t0, 2)
        if r.get("ok"):
            manifest_entries.append({
                "id": r["id"],
                "path": r["id"],
                "source": r["source"],
            })
            print(f"[{i}/{len(paths)}] {r['id']} OK ({elapsed}s)")
        else:
            print(f"[{i}/{len(paths)}] {r['id']} FAIL: {r.get('error')}")
            fail_count += 1
        # 50 件ごとに中間 manifest 保存
        if i % 50 == 0:
            partial_path.write_text(
                json.dumps({"entries": manifest_entries, "failed": fail_count},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    manifest = {
        "name": args.output_name,
        "source": "DeepCAD raw (Onshape parsed JSON)",
        "split": args.split,
        "total": len(manifest_entries),
        "failed": fail_count,
        "scale_normalized_to_mm": 100.0,
        "entries": manifest_entries,
        "structure": {
            "drawing":     "<id>/drawing.png — 2D 線画 4 視点 + bbox 寸法 + Ø ラベル",
            "stl":         "<id>/model.stl — 3D メッシュ（mm 正規化済）",
            "step":        "<id>/model.step — 3D 厳密形状（mm 正規化済）",
            "metadata":    "<id>/metadata.json — bbox / features / extrude_ops",
            "source_json": "<id>/source.json — 元 DeepCAD JSON",
        },
    }
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    partial_path.unlink(missing_ok=True)

    total_time = round(time.time() - started, 1)
    print(f"\n[*] {len(manifest_entries)}/{len(paths)} entries built (failed={fail_count}) in {total_time}s")
    print(f"[*] manifest: {out_root / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
