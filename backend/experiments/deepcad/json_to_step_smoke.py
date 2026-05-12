"""DeepCAD cadlib_ocp の動作確認用 smoke テスト。

1 つの JSON を読み込んで create_CAD → STEP に書き出す。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/experiments/deepcad")

from cadlib_ocp.extrude import CADSequence
from cadlib_ocp.visualize import create_CAD

from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone


def write_step_file(shape, path: str) -> None:
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    status = writer.Write(path)
    if status != IFSelect_RetDone:
        raise RuntimeError(f"STEP write failed: status={status}")


def main(json_path: str, out_step: str = "/tmp/deepcad_smoke.step") -> None:
    print(f"loading {json_path}")
    with open(json_path) as f:
        data = json.load(f)
    cad_seq = CADSequence.from_dict(data)
    print(f"CADSequence parsed: {len(cad_seq.seq)} extrude ops")
    cad_seq.normalize()
    shape = create_CAD(cad_seq)
    write_step_file(shape, out_step)
    print(f"wrote STEP: {out_step}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python json_to_step_smoke.py <path-to.json>")
        sys.exit(1)
    main(sys.argv[1])
