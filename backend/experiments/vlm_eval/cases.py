"""VLM 評価実験の共通データ構造・テストケース定義（v2 — 多様化版）。

Case A v2: より特徴の多い reference を用意し、各特徴の欠落／追加で variant を作る。
- ベース 80×50×20 box
- 多段ボス（φ30×5 + φ20×3）
- 中央スロット 15×5 貫通
- PCD φ40 上 4 穴 (φ4)
- ベース外周 R3 フィレット

variants で各特徴をピンポイントに変更して、VLM の特徴別検出能力をマッピングする。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# ----- 共通定義 ---------------------------------------------------------------
SeverityT = Literal["critical", "major", "minor"]
FeatureT = Literal[
    "outline", "hole", "slot", "boss", "step",
    "chamfer", "fillet", "thread", "dimension", "other",
]


@dataclass(frozen=True)
class Discrepancy:
    feature_type: FeatureT
    description: str
    severity: SeverityT


@dataclass(frozen=True)
class Variant:
    name: str
    cad_script: str
    ground_truth: tuple[Discrepancy, ...]
    note: str = ""


# ----- 参照モデル -------------------------------------------------------------
# 4 PCD 穴の位置（φ40 円周上、45°/135°/225°/315°）
_PCD_PREAMBLE = """\
import cadquery as cq
import math
PCD_R = 20
PCD_4 = [
    (PCD_R*math.cos(math.radians(a)), PCD_R*math.sin(math.radians(a)))
    for a in (45, 135, 225, 315)
]
"""

REFERENCE_SCRIPT = _PCD_PREAMBLE + """
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").tag("base_top")
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(15).extrude(5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(10).extrude(3)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").slot2D(15, 5).cutThruAll()
    .workplaneFromTagged("base_top")
    .pushPoints(PCD_4).hole(4)
    .edges("|Z").fillet(3)
)
"""


# ----- バリアント -------------------------------------------------------------

VARIANTS: tuple[Variant, ...] = (
    Variant(
        name="v1_missing_pcd_hole",
        note="PCD 4 穴のうち 1 つ（315°位置）を削除",
        cad_script=_PCD_PREAMBLE + """
PCD_3 = PCD_4[:3]  # 最後の 1 個を削除
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").tag("base_top")
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(15).extrude(5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(10).extrude(3)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").slot2D(15, 5).cutThruAll()
    .workplaneFromTagged("base_top")
    .pushPoints(PCD_3).hole(4)
    .edges("|Z").fillet(3)
)
""",
        ground_truth=(
            Discrepancy(
                feature_type="hole",
                description="PCD φ40 上の 4 穴のうち 315°位置の 1 個が欠落（4→3 個）",
                severity="critical",
            ),
        ),
    ),
    Variant(
        name="v2_no_fillet",
        note="ベース外周 R3 フィレットを削除",
        cad_script=_PCD_PREAMBLE + """
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").tag("base_top")
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(15).extrude(5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(10).extrude(3)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").slot2D(15, 5).cutThruAll()
    .workplaneFromTagged("base_top")
    .pushPoints(PCD_4).hole(4)
)
""",
        ground_truth=(
            Discrepancy(
                feature_type="fillet",
                description="ベース外周 (Z 軸平行エッジ) の R3 フィレットが欠落、角が直角",
                severity="major",
            ),
        ),
    ),
    Variant(
        name="v3_missing_slot",
        note="中央 15×5 貫通スロットを削除",
        cad_script=_PCD_PREAMBLE + """
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").tag("base_top")
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(15).extrude(5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(10).extrude(3)
    .workplaneFromTagged("base_top")
    .pushPoints(PCD_4).hole(4)
    .edges("|Z").fillet(3)
)
""",
        ground_truth=(
            Discrepancy(
                feature_type="slot",
                description="ボス中央の 15×5 貫通スロット（obround）が欠落",
                severity="critical",
            ),
        ),
    ),
    Variant(
        name="v4_no_boss",
        note="多段ボスを完全削除（ベース box + PCD 穴 + フィレットのみ）。スロットも結果的に消失",
        cad_script=_PCD_PREAMBLE + """
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox")
    .pushPoints(PCD_4).hole(4)
    .edges("|Z").fillet(3)
)
""",
        ground_truth=(
            Discrepancy(
                feature_type="boss",
                description="多段ボス（φ30×5 + φ20×3）が完全に欠落、上面が平坦",
                severity="critical",
            ),
            Discrepancy(
                feature_type="slot",
                description="ボス中央のスロットも欠落（ボス削除に伴う）",
                severity="critical",
            ),
        ),
    ),
    Variant(
        name="v5_partial_boss",
        note="ボス 2 段目（φ20×3）のみ削除、1 段目（φ30×5）は残す",
        cad_script=_PCD_PREAMBLE + """
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").tag("base_top")
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(15).extrude(5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").slot2D(15, 5).cutThruAll()
    .workplaneFromTagged("base_top")
    .pushPoints(PCD_4).hole(4)
    .edges("|Z").fillet(3)
)
""",
        ground_truth=(
            Discrepancy(
                feature_type="boss",
                description="ボスの 2 段目（φ20×3）が欠落、ボスが 1 段だけ（φ30×5）の状態",
                severity="major",
            ),
        ),
    ),
    Variant(
        name="v6_extra_hole",
        note="reference に無い余計な穴をベース角付近に追加（φ3 × 1）",
        cad_script=_PCD_PREAMBLE + """
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").tag("base_top")
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(15).extrude(5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(10).extrude(3)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").slot2D(15, 5).cutThruAll()
    .workplaneFromTagged("base_top")
    .pushPoints(PCD_4).hole(4)
    # 余計な穴: ベース上面の (35, 20) — 角に近い位置
    .workplaneFromTagged("base_top")
    .center(35, 20).hole(3)
    .edges("|Z").fillet(3)
)
""",
        ground_truth=(
            Discrepancy(
                feature_type="hole",
                description="reference には無い、ベース角近く (35, 20) に φ3 の余計な穴が存在",
                severity="major",
            ),
        ),
    ),
)


# ----- ディレクトリ定義 -------------------------------------------------------
EXPERIMENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXPERIMENT_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
RESULTS_DIR = OUTPUT_DIR / "results"


def variant_image_dir(variant_name: str, mode: Literal["shaded", "line"]) -> Path:
    return IMAGES_DIR / variant_name / mode


def reference_image_dir(mode: Literal["shaded", "line"]) -> Path:
    return IMAGES_DIR / "_reference" / mode
