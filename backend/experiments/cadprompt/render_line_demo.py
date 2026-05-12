"""DeepCAD/CADPrompt サンプルを 1 枚の図面風 PNG にレンダリングするデモ。

CADPrompt の各エントリは Python_Code.py を持つ。それを実行して `part` を取り出し、
1. STEP として保存
2. 既存の CadQuerySvgRenderer で 4 視点 PNG を生成
3. 4 視点を **ランダムに配置**（重ならない、サイズも揺らす）してタイトルブロック付き 1 枚の PNG に合成

寸法注釈は付かない（DeepCAD は形状のみ）。
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, "/app")

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont

from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer

EXPERIMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = EXPERIMENT_DIR / "data"
OUT_DIR = EXPERIMENT_DIR / "render_demo_output"


# ------------------------------------------------------------------
# フィーチャ寸法抽出（Ø / R / C など）
# ------------------------------------------------------------------
def extract_features(solid) -> dict:
    """CadQuery Solid から幾何特徴を抽出する。

    返り値 dict:
      "cylinders": [{"radius", "axis_dir", "axis_loc"}]
      "tori":      [{"major_radius", "minor_radius", "loc"}]   # 小 minor = fillet
      "cones":     [{"ref_radius", "semi_angle_deg", "loc"}]   # 45° semi-angle = chamfer
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    import math

    out = {"cylinders": [], "tori": [], "cones": []}
    for face in solid.Faces():
        gt = face.geomType()
        try:
            surf = BRepAdaptor_Surface(face.wrapped)
            if gt == "CYLINDER":
                cyl = surf.Cylinder()
                r = float(cyl.Radius())
                ax = cyl.Axis()
                d = ax.Direction()
                p = ax.Location()
                out["cylinders"].append({
                    "radius": r,
                    "axis_dir": (d.X(), d.Y(), d.Z()),
                    "axis_loc": (p.X(), p.Y(), p.Z()),
                })
            elif gt == "TORUS":
                tor = surf.Torus()
                p = tor.Location().Location()
                out["tori"].append({
                    "major_radius": float(tor.MajorRadius()),
                    "minor_radius": float(tor.MinorRadius()),
                    "loc": (p.X(), p.Y(), p.Z()),
                })
            elif gt == "CONE":
                cone = surf.Cone()
                p = cone.Location().Location()
                out["cones"].append({
                    "ref_radius": float(cone.RefRadius()),
                    "semi_angle_deg": math.degrees(cone.SemiAngle()),
                    "loc": (p.X(), p.Y(), p.Z()),
                })
        except Exception:
            continue
    return out


def summarize_features(features: dict, tol: float = 0.05) -> dict:
    """抽出フィーチャを「Ø/R/C」表記の集約サマリに変換する。

    - 円筒: 半径ごとにグループ化 → Ø(直径) のユニーク値リスト
    - PCD: 同じ半径の円筒が ≥3 個あり、軸が同一方向で軸 loc が原点から等距離なら PCD として検出
    - トーラス: minor_radius を R <r> として列挙（fillet 候補）
    - コーン: semi_angle が 45±2° なら C <ref_radius> として列挙（chamfer 候補）
    """
    import math

    diam_set: dict[float, int] = {}
    for c in features["cylinders"]:
        d = round(c["radius"] * 2.0, 1)
        diam_set[d] = diam_set.get(d, 0) + 1

    # PCD 候補: 同 radius の円筒で軸が同一方向、軸 loc が原点から等距離（半径 R）
    def _norm(v):
        n = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        return (v[0]/n, v[1]/n, v[2]/n) if n > 1e-9 else v

    pcd_list: list[dict] = []
    by_radius: dict[float, list] = {}
    for c in features["cylinders"]:
        by_radius.setdefault(round(c["radius"], 2), []).append(c)
    for r, group in by_radius.items():
        if len(group) < 3:
            continue
        # 軸方向クラスタ
        ref_axis = _norm(group[0]["axis_dir"])
        same_axis = []
        for c in group:
            d = _norm(c["axis_dir"])
            dot = abs(d[0]*ref_axis[0] + d[1]*ref_axis[1] + d[2]*ref_axis[2])
            if dot > 0.99:
                same_axis.append(c)
        if len(same_axis) < 3:
            continue
        # 軸 location の原点距離（軸方向の射影は除く）
        dists: list[float] = []
        for c in same_axis:
            loc = c["axis_loc"]
            # loc から ref_axis への射影成分を引く（軸を通る垂直距離）
            proj = loc[0]*ref_axis[0] + loc[1]*ref_axis[1] + loc[2]*ref_axis[2]
            perp = (loc[0] - proj*ref_axis[0],
                    loc[1] - proj*ref_axis[1],
                    loc[2] - proj*ref_axis[2])
            dists.append(math.sqrt(perp[0]**2 + perp[1]**2 + perp[2]**2))
        if not dists:
            continue
        mean_d = sum(dists) / len(dists)
        spread = max(dists) - min(dists)
        if spread > tol * max(1.0, mean_d):
            continue
        if mean_d < 1.0:
            continue
        pcd_list.append({"pcd_diameter": round(2 * mean_d, 1),
                         "count": len(same_axis),
                         "hole_diameter": round(2 * r, 1)})

    fillet_radii: list[float] = []
    for t in features["tori"]:
        fillet_radii.append(round(t["minor_radius"], 2))
    fillet_radii = sorted(set(fillet_radii))

    chamfer_sizes: list[float] = []
    for c in features["cones"]:
        if abs(c["semi_angle_deg"]) - 45.0 < 2.0:
            chamfer_sizes.append(round(c["ref_radius"], 2))
    chamfer_sizes = sorted(set(chamfer_sizes))

    return {
        "diameters": sorted(diam_set.keys()),
        "pcd": pcd_list,
        "fillets": fillet_radii,
        "chamfers": chamfer_sizes,
    }


# ------------------------------------------------------------------
# レイアウト合成（JIS 第三角法 + タイトルブロック）
# ------------------------------------------------------------------
def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Linux コンテナで利用可能なフォントを順に試す。最後は default にフォールバック。"""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/opt/conda/fonts/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _content_bbox(src: Image.Image, threshold: int = 240) -> tuple[int, int, int, int] | None:
    """画像内の非白領域（描画されたシルエット）の bbox を返す。"""
    gray = src.convert("L")
    # thresholding: 240 以下のピクセルを「描画」とみなす
    binarized = gray.point(lambda p: 0 if p < threshold else 255, mode="L")
    inverted = Image.eval(binarized, lambda x: 255 - x)
    return inverted.getbbox()


def _draw_arrow(draw: ImageDraw.ImageDraw, x: int, y: int, direction: str,
                size: int = 8, color: tuple[int, int, int] = (0, 0, 0)) -> None:
    """寸法線端の矢印（小さい三角形）を描画。

    direction: "left"|"right"|"up"|"down" — 矢じりが向く方向
    """
    if direction == "right":
        draw.polygon([(x, y), (x - size, y - 3), (x - size, y + 3)], fill=color)
    elif direction == "left":
        draw.polygon([(x, y), (x + size, y - 3), (x + size, y + 3)], fill=color)
    elif direction == "down":
        draw.polygon([(x, y), (x - 3, y - size), (x + 3, y - size)], fill=color)
    elif direction == "up":
        draw.polygon([(x, y), (x - 3, y + size), (x + 3, y + size)], fill=color)


def _draw_horizontal_dim(
    draw: ImageDraw.ImageDraw,
    x_left: int, x_right: int, y: int,
    value: float, font: ImageFont.ImageFont,
    color: tuple[int, int, int] = (30, 30, 30),
    witness_offset: int = 6, dim_offset: int = 16,
) -> None:
    """シルエット下に水平寸法線を描画。

    x_left, x_right: シルエットの左右端 x 座標。
    y: シルエットの下端 y 座標。
    """
    yy = y + dim_offset
    # witness lines（補助線）
    draw.line([(x_left, y + witness_offset), (x_left, yy + 6)], fill=color, width=1)
    draw.line([(x_right, y + witness_offset), (x_right, yy + 6)], fill=color, width=1)
    # 本体（寸法線）
    draw.line([(x_left, yy), (x_right, yy)], fill=color, width=1)
    # 矢印
    _draw_arrow(draw, x_left, yy, "left", color=color)
    _draw_arrow(draw, x_right, yy, "right", color=color)
    # 文字
    text = f"{value:.1f}"
    try:
        tw = int(draw.textlength(text, font=font))
    except Exception:
        tw = len(text) * 9
    tx = (x_left + x_right) // 2 - tw // 2
    # テキスト下地（線と被らないよう小さい白パッチ）
    draw.rectangle([tx - 4, yy - 22, tx + tw + 4, yy - 4], fill=(255, 255, 255))
    draw.text((tx, yy - 22), text, fill=color, font=font)


def _draw_vertical_dim(
    draw: ImageDraw.ImageDraw,
    y_top: int, y_bottom: int, x: int,
    value: float, font: ImageFont.ImageFont,
    color: tuple[int, int, int] = (30, 30, 30),
    witness_offset: int = 6, dim_offset: int = 16,
) -> None:
    """シルエット右側に垂直寸法線を描画。"""
    xx = x + dim_offset
    draw.line([(x + witness_offset, y_top), (xx + 6, y_top)], fill=color, width=1)
    draw.line([(x + witness_offset, y_bottom), (xx + 6, y_bottom)], fill=color, width=1)
    draw.line([(xx, y_top), (xx, y_bottom)], fill=color, width=1)
    _draw_arrow(draw, xx, y_top, "up", color=color)
    _draw_arrow(draw, xx, y_bottom, "down", color=color)
    text = f"{value:.1f}"
    try:
        tw = int(draw.textlength(text, font=font))
    except Exception:
        tw = len(text) * 9
    ty = (y_top + y_bottom) // 2 - 12
    draw.rectangle([xx + 4, ty - 2, xx + 4 + tw + 8, ty + 22], fill=(255, 255, 255))
    draw.text((xx + 8, ty), text, fill=color, font=font)


def _project_to_view(world_xyz: tuple[float, float, float], view: str) -> tuple[float, float] | None:
    """world 座標を各正面図の screen 座標 (mm) に投影。

    返り値は (右が正の水平 mm, 下が正の垂直 mm) の符号付き値。
    iso は None。

    投影規約は views.py に従う（top: +Z 視点 / front: -Y 視点 / side: +X 視点）。
    """
    x, y, z = world_xyz
    if view == "top":
        return (x, -y)   # PIL Y は下方向正
    if view == "front":
        return (x, -z)
    if view == "side":
        return (-y, -z)
    return None


def _draw_diameter_label(
    canvas: Image.Image,
    img_origin: tuple[int, int],
    img_size: tuple[int, int],
    silhouette_bbox_canvas: tuple[int, int, int, int],
    bbox_world_extent: tuple[float, float],
    feature_loc_world: tuple[float, float],
    diameter_mm: float,
    font: ImageFont.ImageFont,
) -> None:
    """円フィーチャに Ø ラベルとリーダー線を描画する。

    img_origin: ビュー貼り付けの左上（canvas 座標）
    img_size: ビュー貼り付けサイズ（pw, ph）
    silhouette_bbox_canvas: 検出されたシルエット bbox（canvas 座標）
    bbox_world_extent: ビュー上の (水平 mm, 垂直 mm) — 寸法ラベル用と同じ
    feature_loc_world: ビュー投影後の (右が正 mm, 下が正 mm)
    """
    sl, st_, sr, sb = silhouette_bbox_canvas
    sw_px = sr - sl
    sh_px = sb - st_
    w_mm, h_mm = bbox_world_extent
    if w_mm <= 0 or h_mm <= 0 or sw_px <= 0 or sh_px <= 0:
        return

    # ピクセル/mm スケール（シルエット幅 ÷ 世界幅）
    sx_per_mm = sw_px / w_mm
    sy_per_mm = sh_px / h_mm

    # シルエット中央を世界 (0,0) と仮定（モデルは scaling 後に origin 中心）
    cx = (sl + sr) / 2
    cy = (st_ + sb) / 2

    fx_mm, fy_mm = feature_loc_world
    px = int(cx + fx_mm * sx_per_mm)
    py = int(cy + fy_mm * sy_per_mm)

    # 半径を画面ピクセルへ換算（円の場合は等比なので horizontal scale を採用）
    radius_px = int((diameter_mm / 2.0) * sx_per_mm)
    if radius_px < 4:
        return

    # リーダー線: 円の中心 → 円外（45° 方向）→ ラベルへの水平折り返し
    import math
    angle = math.radians(45)
    edge_x = px + int(radius_px * math.cos(angle))
    edge_y = py - int(radius_px * math.sin(angle))
    leader_end_x = edge_x + 30
    leader_end_y = edge_y - 30

    draw = ImageDraw.Draw(canvas)
    color = (30, 30, 30)
    draw.line([(edge_x, edge_y), (leader_end_x, leader_end_y)], fill=color, width=1)
    draw.line([(leader_end_x, leader_end_y), (leader_end_x + 60, leader_end_y)], fill=color, width=1)
    text = f"Ø{diameter_mm:.1f}"  # Ø<value>
    try:
        tw = int(draw.textlength(text, font=font))
    except Exception:
        tw = len(text) * 9
    tx = leader_end_x + 4
    ty = leader_end_y - 22
    draw.rectangle([tx - 3, ty - 1, tx + tw + 6, ty + 22], fill=(255, 255, 255))
    draw.text((tx, ty), text, fill=color, font=font)


def _paste_view_at(
    canvas: Image.Image,
    view_png: bytes,
    pos: tuple[int, int],
    size: tuple[int, int],
    dims_mm: tuple[float, float] | None,
    font: ImageFont.ImageFont,
    view_name: str | None = None,
    cylinders: list[dict] | None = None,
) -> None:
    """1 視点を canvas に貼り付け、必要なら寸法線をオーバーレイする。

    pos: 貼り付け位置（左上）。size: 貼り付けサイズ（最大）。
    dims_mm: (水平寸法 mm, 垂直寸法 mm)、または None（iso 等）。
    枠・ラベルは描画しない。
    """
    px, py = pos
    pw, ph = size

    src = Image.open(BytesIO(view_png)).convert("RGB")
    src.thumbnail((pw, ph), Image.LANCZOS)
    sx = px + (pw - src.width) // 2
    sy = py + (ph - src.height) // 2
    canvas.paste(src, (sx, sy))

    if dims_mm is None:
        return

    # シルエット bbox を src 内で検出 → canvas 座標に変換
    bbox = _content_bbox(src)
    if bbox is None:
        return
    cl = sx + bbox[0]
    ct = sy + bbox[1]
    cr = sx + bbox[2]
    cb = sy + bbox[3]

    draw = ImageDraw.Draw(canvas)
    horiz_mm, vert_mm = dims_mm
    _draw_horizontal_dim(draw, cl, cr, cb, horiz_mm, font)
    _draw_vertical_dim(draw, ct, cb, cr, vert_mm, font)

    # 円フィーチャの Ø ラベル（円柱軸が視線と平行＝この視点で円として見える）
    if view_name and cylinders:
        # 視線方向の単位ベクトル
        view_dir = {
            "top":   (0.0, 0.0, 1.0),
            "front": (0.0, -1.0, 0.0),
            "side":  (1.0, 0.0, 0.0),
        }.get(view_name)
        if view_dir is None:
            return
        seen_diam: set[float] = set()
        for c in cylinders:
            ax = c["axis_dir"]
            dot = abs(ax[0]*view_dir[0] + ax[1]*view_dir[1] + ax[2]*view_dir[2])
            if dot < 0.99:
                continue
            d_mm = round(c["radius"] * 2.0, 1)
            # 同じ Ø で同じ位置なら重複描画を避ける
            loc_proj = _project_to_view(c["axis_loc"], view_name)
            if loc_proj is None:
                continue
            key = (d_mm, round(loc_proj[0], 1), round(loc_proj[1], 1))
            if key in seen_diam:
                continue
            seen_diam.add(key)
            _draw_diameter_label(
                canvas,
                img_origin=(sx, sy),
                img_size=(src.width, src.height),
                silhouette_bbox_canvas=(cl, ct, cr, cb),
                bbox_world_extent=dims_mm,
                feature_loc_world=loc_proj,
                diameter_mm=d_mm,
                font=font,
            )


def _random_non_overlapping_positions(
    area: tuple[int, int, int, int],
    sizes: list[tuple[int, int]],
    rng: random.Random,
    max_tries: int = 600,
    margin: int = 30,
) -> list[tuple[int, int]]:
    """area 内に n 個の固定サイズ矩形をランダム配置（重ならない位置のみ揺らす）。

    return: 各矩形の左上 (x, y) のリスト。配置できなければ grid フォールバック。
    """
    a_left, a_top, a_right, a_bottom = area
    placed: list[tuple[int, int, int, int]] = []
    positions: list[tuple[int, int]] = []

    def overlaps(box: tuple[int, int, int, int]) -> bool:
        l, t, r, b = box
        for ll, tt, rr, bb in placed:
            if not (r + margin <= ll or rr + margin <= l
                    or b + margin <= tt or bb + margin <= t):
                return True
        return False

    for w, h in sizes:
        ok = False
        for _ in range(max_tries):
            if a_right - w <= a_left or a_bottom - h <= a_top:
                break
            x = rng.randint(a_left, a_right - w)
            y = rng.randint(a_top, a_bottom - h)
            box = (x, y, x + w, y + h)
            if not overlaps(box):
                placed.append(box)
                positions.append((x, y))
                ok = True
                break
        if not ok:
            # フォールバック: 2x2 grid で埋める
            n = len(sizes)
            cols = 2
            rows = (n + cols - 1) // cols
            cell_w = (a_right - a_left) // cols
            cell_h = (a_bottom - a_top) // rows
            idx = len(positions)
            cx = idx % cols
            cy = idx // cols
            x = a_left + cx * cell_w + (cell_w - w) // 2
            y = a_top + cy * cell_h + (cell_h - h) // 2
            positions.append((x, y))
            placed.append((x, y, x + w, y + h))

    return positions


def compose_drawing_sheet(
    obj_id: str,
    views_top: bytes,
    views_front: bytes,
    views_side: bytes,
    views_iso: bytes,
    bbox_mm: tuple[float, float, float],
    features_summary: dict | None = None,
    cylinders: list[dict] | None = None,
    sheet_size: tuple[int, int] = (2200, 1600),
    margin: int = 30,
    view_size: tuple[int, int] = (520, 460),
    title: str = "DRAWING",
    note: str = "",
    seed: int | None = None,
) -> bytes:
    """4 視点を 1 枚の図面風 PNG に合成する。

    - サイズは 4 視点とも `view_size` 固定
    - 位置のみランダム（重ならない）
    - 各視点に寸法線をオーバーレイ（iso は除く）
    - 視点ごとのラベル・枠は描画しない
    - タイトルブロックは下部固定

    bbox_mm: (xlen, ylen, zlen) を mm で渡す。各視点に表示する寸法に使う。
    """
    W, H = sheet_size
    xlen, ylen, zlen = bbox_mm

    canvas = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # 外枠（製図ボーダー）
    border = (20, 20, 20)
    draw.rectangle([margin, margin, W - margin, H - margin], outline=border, width=3)

    tb_h = 110
    area = (margin + 6, margin + 6, W - margin - 6, H - margin - tb_h - 6)

    label_font = _load_font(22)
    title_font = _load_font(28)
    body_font = _load_font(20)
    dim_font = _load_font(20)

    rng = random.Random(seed if seed is not None else hash(obj_id) & 0xFFFFFFFF)

    # ビュー → 表示寸法（horizontal, vertical in mm） + 視点名
    # 投影向き: top=+Z, front=-Y, side=+X, iso=skip
    views_with_dims = [
        ("top",   views_top,   (xlen, ylen)),
        ("front", views_front, (xlen, zlen)),
        ("side",  views_side,  (ylen, zlen)),
        ("iso",   views_iso,   None),
    ]
    rng.shuffle(views_with_dims)

    sizes = [view_size] * 4
    positions = _random_non_overlapping_positions(area, sizes, rng)

    for (view_name, view_png, dims_mm), pos in zip(views_with_dims, positions):
        _paste_view_at(
            canvas, view_png, pos, view_size, dims_mm, dim_font,
            view_name=view_name,
            cylinders=cylinders or [],
        )

    # タイトルブロック
    tb_top = H - margin - tb_h
    tb_left = margin + 6
    tb_right = W - margin - 6
    draw.rectangle([tb_left, tb_top, tb_right, H - margin - 6], outline=border, width=2)
    col1 = tb_left + 700
    col2 = tb_left + 1300
    draw.line([(col1, tb_top), (col1, H - margin - 6)], fill=border, width=1)
    draw.line([(col2, tb_top), (col2, H - margin - 6)], fill=border, width=1)
    draw.line([(tb_left, tb_top + tb_h // 2), (col1, tb_top + tb_h // 2)], fill=border, width=1)

    draw.text((tb_left + 12, tb_top + 8), "TITLE", fill=border, font=label_font)
    draw.text((tb_left + 12, tb_top + tb_h // 2 + 8), "PART NO.", fill=border, font=label_font)
    draw.text((col1 + 12, tb_top + 8), "PROJECTION", fill=border, font=label_font)
    draw.text((col2 + 12, tb_top + 8), "NOTES", fill=border, font=label_font)

    draw.text((tb_left + 90, tb_top + 8), title, fill=(30, 30, 30), font=title_font)
    draw.text((tb_left + 130, tb_top + tb_h // 2 + 8), obj_id, fill=(30, 30, 30), font=body_font)
    draw.text((col1 + 160, tb_top + 8), "Third-angle (JIS B 0001)", fill=(30, 30, 30), font=body_font)
    draw.text((col1 + 12, tb_top + tb_h // 2 + 8), "UNIT: mm   SCALE: NTS",
              fill=(30, 30, 30), font=body_font)
    # NOTES 内容: フィーチャ寸法サマリ
    note_text = note
    if features_summary:
        parts: list[str] = []
        diams = features_summary.get("diameters", [])
        if diams:
            parts.append("Ø: " + ", ".join(f"{d:.1f}" for d in diams))
        pcds = features_summary.get("pcd", [])
        for p in pcds:
            parts.append(f"PCD Ø{p['pcd_diameter']:.1f}× {p['count']}-Ø{p['hole_diameter']:.1f}")
        fillets = features_summary.get("fillets", [])
        if fillets:
            parts.append("R: " + ", ".join(f"{r:.1f}" for r in fillets))
        chamfers = features_summary.get("chamfers", [])
        if chamfers:
            parts.append("C: " + ", ".join(f"{c:.1f}" for c in chamfers))
        if parts:
            note_text = "  ".join(parts)

    draw.text((col2 + 12, tb_top + tb_h // 2 + 8), note_text or "(no annotations)",
              fill=(30, 30, 30), font=body_font)

    out = BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()


# ------------------------------------------------------------------
# 1 サンプル処理
# ------------------------------------------------------------------
def run_one(entry_dir: Path, renderer: CadQuerySvgRenderer) -> dict:
    obj_id = entry_dir.name
    out_subdir = OUT_DIR / obj_id
    out_subdir.mkdir(parents=True, exist_ok=True)

    code_path = entry_dir / "Python_Code.py"
    code = code_path.read_text(encoding="utf-8")

    namespace: dict = {}
    cwd = os.getcwd()
    os.chdir(str(out_subdir))
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
    scale = target / max_extent if max_extent > 1e-9 else 1.0
    if abs(scale - 1.0) > 1e-6:
        try:
            scaled_part = part.translate((-bbox.center.x, -bbox.center.y, -bbox.center.z))
        except Exception:
            scaled_part = part
        s = scaled_part.val() if hasattr(scaled_part, "val") else scaled_part
        scaled_solid = s.scale(scale)
        part = cq.Workplane().add(scaled_solid)

    # スケール後の bbox（mm 単位）を取得
    scaled_solid = part.val() if hasattr(part, "val") else part
    sb = scaled_solid.BoundingBox()
    bbox_mm = (sb.xlen, sb.ylen, sb.zlen)

    # フィーチャ抽出（Ø / R / C / PCD）
    raw_features = extract_features(scaled_solid)
    features_summary = summarize_features(raw_features)

    # STEP 出力
    step_path = out_subdir / f"{obj_id}.step"
    cq.exporters.export(part, str(step_path))

    # 4 視点取得
    views = renderer.render(str(step_path))

    # 4 視点を 1 枚の図面風 PNG に合成
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
    sheet_path = out_subdir / f"{obj_id}_sheet.png"
    sheet_path.write_bytes(sheet_png)

    return {"id": obj_id, "ok": True, "sheet": str(sheet_path), "step": str(step_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", default="00995843,00007258,00001615,00998088,00520402",
                        help="カンマ区切りの ID リスト")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    renderer = CadQuerySvgRenderer()

    ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    print(f"=== render_drawing_sheet: {len(ids)} entries ===\n")
    for obj_id in ids:
        entry = DATA_DIR / obj_id
        if not entry.is_dir():
            print(f"[skip] {obj_id}: not found")
            continue
        try:
            r = run_one(entry, renderer)
        except Exception as e:
            import traceback
            print(f"[FAIL] {obj_id}: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue
        if r["ok"]:
            print(f"[OK] {obj_id}: {r['sheet']}")
        else:
            print(f"[FAIL] {obj_id}: {r.get('error')}")
    print(f"\n[*] all sheets under {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
