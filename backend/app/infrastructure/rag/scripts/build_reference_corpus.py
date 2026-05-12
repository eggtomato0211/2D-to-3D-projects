"""DeepCAD train split から Reference Code corpus を構築。

実行:
    docker compose run --rm backend python -m app.infrastructure.rag.scripts.build_reference_corpus -n 10000

出力先:
    /app/app/infrastructure/rag/reference_codes/<id>.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/experiments/deepcad")

DATA_DIR = Path("/app/experiments/deepcad/data/cad_json")
SPLIT_FILE = Path("/app/experiments/deepcad/data/train_val_test_split.json")
OUT_DIR = Path("/app/app/infrastructure/rag/reference_codes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=10000)
    parser.add_argument("--split", choices=["train", "validation", "test"], default="train")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # train split の ID を読む
    split_data = json.loads(SPLIT_FILE.read_text())
    ids = split_data.get(args.split, [])
    print(f"=== build_reference_corpus: {args.split} split has {len(ids)} ids ===\n")

    # サンプリング
    rng = random.Random(args.seed)
    sampled = rng.sample(ids, min(args.num_samples, len(ids)))
    sampled.sort()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 既存処理 (build_dataset の internals) を再利用するための import
    import cadquery as cq
    from cadlib_ocp.extrude import CADSequence
    from cadlib_ocp.visualize import create_CAD
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.IFSelect import IFSelect_RetDone

    from experiments.cadprompt.render_line_demo import (
        extract_features, summarize_features,
    )
    from app.infrastructure.rag.reference_corpus import build_reference_entry

    def write_step(shape, path: Path) -> None:
        w = STEPControl_Writer()
        w.Transfer(shape, STEPControl_AsIs)
        if w.Write(str(path)) != IFSelect_RetDone:
            raise RuntimeError("STEP write failed")

    success = 0
    fail = 0
    skipped = 0
    started = time.time()
    tmp_dir = Path("/tmp/refcorpus_work")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for i, fid in enumerate(sampled, 1):
        out_path = OUT_DIR / f"{fid.replace('/', '_')}.json"
        if out_path.exists():
            skipped += 1
            continue
        json_path = DATA_DIR / f"{fid}.json"
        if not json_path.exists():
            fail += 1
            continue
        try:
            data = json.loads(json_path.read_text())
            seq = CADSequence.from_dict(data)
            seq.normalize()
            shape = create_CAD(seq)
            if not BRepCheck_Analyzer(shape).IsValid():
                fail += 1
                continue
            # STEP に書き出し→ CadQuery 読み込みで正規化済 bbox を得る
            raw_step = tmp_dir / f"{i}.step"
            write_step(shape, raw_step)
            imported = cq.importers.importStep(str(raw_step))
            solid = imported.val()
            bbox = solid.BoundingBox()
            max_ext = max(bbox.xlen, bbox.ylen, bbox.zlen)
            if max_ext < 1e-9:
                fail += 1
                continue
            scale = 100.0 / max_ext
            centered = imported.translate((-bbox.center.x, -bbox.center.y, -bbox.center.z))
            scaled_solid = centered.val().scale(scale)
            sb = scaled_solid.BoundingBox()
            bbox_mm = {"x": sb.xlen, "y": sb.ylen, "z": sb.zlen}
            raw_features = extract_features(scaled_solid)
            features_summary = summarize_features(raw_features)

            obj_id = fid.split("/")[-1]
            entry = build_reference_entry(
                obj_id=obj_id,
                json_data=data,
                bbox_mm=bbox_mm,
                features_summary=features_summary,
                extrude_ops=len(seq.seq),
            )
            out_path.write_text(json.dumps(asdict(entry), ensure_ascii=False), encoding="utf-8")
            success += 1
        except Exception as e:
            fail += 1
            if fail <= 5:
                print(f"  [FAIL] {fid}: {type(e).__name__}: {str(e)[:80]}")
        finally:
            try:
                (tmp_dir / f"{i}.step").unlink(missing_ok=True)
            except Exception:
                pass

        if i % 500 == 0:
            elapsed = time.time() - started
            print(f"  [{i}/{len(sampled)}] success={success}, fail={fail}, skipped={skipped} ({elapsed:.0f}s)")

    elapsed = time.time() - started
    print(f"\n=== done: success={success}, fail={fail}, skipped={skipped} in {elapsed:.0f}s ===")
    print(f"output: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
