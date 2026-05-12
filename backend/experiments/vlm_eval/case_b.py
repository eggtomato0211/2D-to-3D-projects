"""Case B: 実図面と生成失敗例の比較

RING 部品（FF1-K9792SDA）の図面と、過去のプロジェクトで実際に観測された
失敗生成例を比較し、VLM が現実の不一致を検出できるかを評価する。

reference は CadQuery で生成しない（実図面 PNG を使う）ため、
通常の Case A とは異なるフローを取る。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cases import Discrepancy

CASE_B_DIR = Path(__file__).resolve().parent / "cases_b"


@dataclass(frozen=True)
class CaseBVariant:
    """実図面 vs 候補モデルの比較ケース"""
    name: str
    drawing_path: Path             # 元 2D 図面の画像パス
    candidate_cad_script: str      # 候補となる失敗生成例の CadQuery スクリプト
    ground_truth: tuple[Discrepancy, ...]
    note: str = ""


# ---- RING 部品の失敗生成例の再現 ----
# 元図面 (drawing.png) には以下の特徴がある:
# - φ53.95 外径
# - 4-R6 外周スカラップ切欠き
# - 中央 5 幅 obround スロット（貫通）
# - 多段ボス（φ50 / φ31.85 / φ30 内側凹み）
# - PCD φ42 上 6 穴（2-φ4.5 サラ + 4-M3 タップ）
# - 全周 C0.5 面取り
# - 縦エッジ R3 等のフィレット
#
# 失敗生成例は: 外周ディスク + 4 スカラップ + 中央大穴 + 上部小穴 1 個
# （多段ボス、長穴、PCD 6 穴の大半が欠落）

RING_FAILED_CANDIDATE_SCRIPT = """\
import cadquery as cq

# ベースディスク φ54 厚さ 3
result = cq.Workplane("XY").circle(27).extrude(3)

# 外周 4-R6 スカラップ切欠き（90° おき、 45°/135°/225°/315°）
# ここは正しく再現されている
cutter = (
    cq.Workplane("XY")
    .polarArray(radius=27, startAngle=45, angle=360, count=4)
    .circle(6)
    .extrude(3)
)
result = result.cut(cutter)

# 中央大穴 (φ20) — 元図面のスロット形状を理解できず単純な丸穴に
result = result.faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(20)

# 上部に 1 つだけ小穴 — 元図面では PCD φ42 上に 6 穴あるはずが 1 個のみ
result = (
    result.faces(">Z").workplane(centerOption="CenterOfBoundBox")
    .center(0, 18).hole(3)
)
"""


CASE_B_VARIANTS: tuple[CaseBVariant, ...] = (
    CaseBVariant(
        name="ring_failed_v1",
        drawing_path=CASE_B_DIR / "ring" / "drawing.png",
        candidate_cad_script=RING_FAILED_CANDIDATE_SCRIPT,
        note="2026-04 観測の失敗生成例。多段ボス・長穴・PCD 穴がほぼ欠落",
        ground_truth=(
            Discrepancy(
                feature_type="slot",
                description="中央 5 幅の obround スロット（貫通）が欠落、代わりに丸穴になっている",
                severity="critical",
            ),
            Discrepancy(
                feature_type="boss",
                description="多段ボス（φ50/φ31.85/φ30）が完全に欠落、平板になっている",
                severity="critical",
            ),
            Discrepancy(
                feature_type="hole",
                description="PCD φ42 上の 6 穴（2-φ4.5 + 4-M3）のうち 5 個が欠落、1 個のみ存在",
                severity="critical",
            ),
            Discrepancy(
                feature_type="hole",
                description="2-φ4.5 穴の裏側 φ8.8 サラ（counterbore）が欠落",
                severity="major",
            ),
            Discrepancy(
                feature_type="chamfer",
                description="全周 C0.5 面取りが欠落（ただし線画では検出困難な可能性大）",
                severity="minor",
            ),
            Discrepancy(
                feature_type="dimension",
                description="外径が概ね一致するも、厚みが元図面の段付き構造を反映していない",
                severity="major",
            ),
        ),
    ),
)
