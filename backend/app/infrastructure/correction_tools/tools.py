"""§10.6 Tool Use 化: LLM が呼び出せる構造化ツールの定義。

各ツールは:
  - Anthropic tool use 用の JSON Schema（spec）
  - パラメータを受け取って CadQuery コード片を生成する関数（codegen）

LLM は自然言語でコードを書く代わりにこれらを呼び出す。サーバ側で
コード片を生成・既存 result 変数に対する追加チェーンとして連結する。
これにより `R3 (LLM のコード surgery が脆い)` を抜本的に回避する。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    """1 ツールのインターフェース定義 + コード生成器"""
    name: str
    description: str
    input_schema: dict
    codegen: Callable[[dict], str]

    def anthropic_definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


# ---- 個別ツール ---------------------------------------------------------------

def _gen_add_hole(args: dict) -> str:
    x = args["x"]
    y = args["y"]
    d = args["diameter"]
    face = args.get("on_face", "top")
    selector = ">Z" if face == "top" else "<Z"
    return (
        f'\nresult = (result.faces("{selector}")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.center({x}, {y}).hole({d}))\n'
    )


_ADD_HOLE = ToolSpec(
    name="add_hole",
    description=(
        "Add a circular through-hole at a specified (x, y) position on the top or bottom face. "
        "Coordinates are in mm, measured from the center of the bounding box. "
        "Use this for individual missing holes."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "x": {"type": "number", "description": "X coordinate of hole center in mm (relative to bbox center)"},
            "y": {"type": "number", "description": "Y coordinate of hole center in mm"},
            "diameter": {"type": "number", "description": "Hole diameter in mm. For M-thread holes, use minor (pilot) diameter: M3=2.5, M4=3.3, M5=4.2, M6=5.0"},
            "on_face": {"type": "string", "enum": ["top", "bottom"], "description": "Face on which the hole starts (default top)"},
        },
        "required": ["x", "y", "diameter"],
    },
    codegen=_gen_add_hole,
)


def _gen_add_pcd_holes(args: dict) -> str:
    r = args["pcd_radius"]
    n = args["count"]
    start = args.get("start_angle_deg", 0)
    d = args["diameter"]
    angle = args.get("total_angle_deg", 360)
    face = args.get("on_face", "top")
    selector = ">Z" if face == "top" else "<Z"
    return (
        f'\nresult = (result.faces("{selector}")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.polarArray(radius={r}, startAngle={start}, angle={angle}, count={n})'
        f'.hole({d}))\n'
    )


_ADD_PCD_HOLES = ToolSpec(
    name="add_pcd_holes",
    description=(
        "Add N holes equally spaced on a pitch circle (PCD). "
        "Use for `N-φX PCD φ<2*pcd_radius>` patterns from drawings. "
        "For asymmetric layouts (e.g. 2 holes 180° apart), set total_angle_deg to span only those positions."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pcd_radius": {"type": "number", "description": "Pitch circle radius in mm (= PCD/2)"},
            "count": {"type": "integer", "description": "Number of holes"},
            "start_angle_deg": {"type": "number", "description": "Starting angle in degrees (default 0)"},
            "total_angle_deg": {"type": "number", "description": "Angular span (default 360 for full equal spacing). Use 180 for 2 opposed holes"},
            "diameter": {"type": "number", "description": "Hole diameter in mm. For M-thread, use pilot d: M3=2.5, M4=3.3"},
            "on_face": {"type": "string", "enum": ["top", "bottom"]},
        },
        "required": ["pcd_radius", "count", "diameter"],
    },
    codegen=_gen_add_pcd_holes,
)


def _gen_cut_obround_slot(args: dict) -> str:
    x = args.get("x", 0)
    y = args.get("y", 0)
    L = args["length"]
    w = args["width"]
    angle = args.get("rotation_deg", 0)
    return (
        f'\nresult = (result.faces(">Z")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.center({x}, {y})'
        + (f'.transformed(rotate=(0, 0, {angle}))' if angle else '')
        + f'.slot2D(length={L}, diameter={w})'
        f'.cutThruAll())\n'
    )


_CUT_OBROUND_SLOT = ToolSpec(
    name="cut_obround_slot",
    description=(
        "Cut a through obround (stadium-shaped) slot. "
        "Use for `中央 X 幅 obround 貫通` patterns. "
        "length is the total outer-to-outer length (including end caps); width is the slot width."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "x": {"type": "number", "description": "X center (default 0)"},
            "y": {"type": "number", "description": "Y center (default 0)"},
            "length": {"type": "number", "description": "Total outer length of slot in mm"},
            "width": {"type": "number", "description": "Slot width in mm (e.g. 5 for `中央5幅 obround`)"},
            "rotation_deg": {"type": "number", "description": "Rotation in degrees (default 0=along X axis)"},
        },
        "required": ["length", "width"],
    },
    codegen=_gen_cut_obround_slot,
)


def _gen_add_counterbore(args: dict) -> str:
    x = args["x"]
    y = args["y"]
    hole_d = args["hole_diameter"]
    cb_d = args["counterbore_diameter"]
    depth = args["counterbore_depth"]
    face = args.get("on_face", "back")
    selector = "<Z" if face == "back" else ">Z"
    return (
        f'\nresult = (result.faces("{selector}")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.center({x}, {y})'
        f'.cboreHole({hole_d}, {cb_d}, {depth}))\n'
    )


_ADD_COUNTERBORE = ToolSpec(
    name="add_counterbore",
    description=(
        "Add a counterbore (ザグリ) hole on the back or top face. "
        "Use for `裏よりφX サラ` patterns in drawings (back-side counterbore for screw heads)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "x": {"type": "number"},
            "y": {"type": "number"},
            "hole_diameter": {"type": "number", "description": "Through-hole diameter (e.g. 4.5 for 2-φ4.5)"},
            "counterbore_diameter": {"type": "number", "description": "Counterbore (larger) diameter (e.g. 8.8)"},
            "counterbore_depth": {"type": "number", "description": "Counterbore depth in mm"},
            "on_face": {"type": "string", "enum": ["top", "back"], "description": "default 'back' (裏より)"},
        },
        "required": ["x", "y", "hole_diameter", "counterbore_diameter", "counterbore_depth"],
    },
    codegen=_gen_add_counterbore,
)


def _gen_add_pcd_counterbores(args: dict) -> str:
    r = args["pcd_radius"]
    n = args["count"]
    start = args.get("start_angle_deg", 0)
    angle = args.get("total_angle_deg", 360)
    hole_d = args["hole_diameter"]
    cb_d = args["counterbore_diameter"]
    depth = args["counterbore_depth"]
    face = args.get("on_face", "back")
    selector = "<Z" if face == "back" else ">Z"
    return (
        f'\nresult = (result.faces("{selector}")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.polarArray(radius={r}, startAngle={start}, angle={angle}, count={n})'
        f'.cboreHole({hole_d}, {cb_d}, {depth}))\n'
    )


_ADD_PCD_COUNTERBORES = ToolSpec(
    name="add_pcd_counterbores",
    description=(
        "Add N counterbore holes equally spaced on a PCD. "
        "Use for `N-φX 裏よりφY サラ PCD φZ` patterns (e.g. `2-φ4.5 裏よりφ8.8 サラ`)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pcd_radius": {"type": "number"},
            "count": {"type": "integer"},
            "start_angle_deg": {"type": "number"},
            "total_angle_deg": {"type": "number", "description": "Angular span (180 for 2 opposed)"},
            "hole_diameter": {"type": "number"},
            "counterbore_diameter": {"type": "number"},
            "counterbore_depth": {"type": "number"},
            "on_face": {"type": "string", "enum": ["top", "back"]},
        },
        "required": ["pcd_radius", "count", "hole_diameter", "counterbore_diameter", "counterbore_depth"],
    },
    codegen=_gen_add_pcd_counterbores,
)


def _gen_add_step_boss(args: dict) -> str:
    d = args["diameter"]
    h = args["height"]
    return (
        f'\nresult = (result.faces(">Z")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.circle({d/2}).extrude({h}))\n'
    )


_ADD_STEP_BOSS = ToolSpec(
    name="add_step_boss",
    description=(
        "Add a circular boss (step) of given diameter and height on top of the current top face. "
        "Stack multiple calls to build multi-step bosses (call once per step, largest first)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "diameter": {"type": "number", "description": "Boss diameter in mm"},
            "height": {"type": "number", "description": "Boss height (extrusion) in mm"},
        },
        "required": ["diameter", "height"],
    },
    codegen=_gen_add_step_boss,
)


def _gen_add_recess(args: dict) -> str:
    d = args["diameter"]
    depth = args["depth"]
    face = args.get("on_face", "top")
    selector = ">Z" if face == "top" else "<Z"
    return (
        f'\nresult = (result.faces("{selector}")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.circle({d/2}).cutBlind({-abs(depth)}))\n'
    )


_ADD_RECESS = ToolSpec(
    name="add_recess",
    description=(
        "Add a circular recess (blind hole / pocket) of given diameter and depth into the top or back face. "
        "Use for `φX 凹み` features."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "diameter": {"type": "number"},
            "depth": {"type": "number", "description": "Recess depth in mm (positive)"},
            "on_face": {"type": "string", "enum": ["top", "back"]},
        },
        "required": ["diameter", "depth"],
    },
    codegen=_gen_add_recess,
)


def _gen_add_chamfer_top_bottom(args: dict) -> str:
    c = args["chamfer"]
    return (
        f'\ntry:\n'
        f'    result = result.edges(">Z or <Z").chamfer({c})\n'
        f'except Exception:\n'
        f'    pass  # chamfer skipped if edge geometry forbids it\n'
    )


_ADD_CHAMFER_TOP_BOTTOM = ToolSpec(
    name="add_chamfer_top_bottom",
    description=(
        "Add a chamfer of given size on all top and bottom edges. "
        "Use for `全周CX 反対側も含む` (all-around chamfer both sides)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "chamfer": {"type": "number", "description": "Chamfer size in mm (e.g. 0.5 for C0.5)"},
        },
        "required": ["chamfer"],
    },
    codegen=_gen_add_chamfer_top_bottom,
)


def _gen_add_fillet_vertical(args: dict) -> str:
    r = args["radius"]
    return (
        f'\ntry:\n'
        f'    result = result.edges("|Z").fillet({r})\n'
        f'except Exception:\n'
        f'    pass\n'
    )


_ADD_FILLET_VERTICAL = ToolSpec(
    name="add_fillet_vertical_edges",
    description=(
        "Add a fillet (rounded corner) of given radius on all Z-axis-parallel edges. "
        "Use for `R<X> 縦エッジフィレット` patterns."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "radius": {"type": "number", "description": "Fillet radius in mm"},
        },
        "required": ["radius"],
    },
    codegen=_gen_add_fillet_vertical,
)


def _gen_cut_outer_scallops(args: dict) -> str:
    r = args["pcd_radius"]
    n = args["count"]
    start = args.get("start_angle_deg", 45)
    sr = args["scallop_radius"]
    h = args["part_thickness"]
    return (
        f'\n_cutter = (cq.Workplane("XY").workplane(offset=-{h})'
        f'.polarArray(radius={r}, startAngle={start}, angle=360, count={n})'
        f'.circle({sr}).extrude({h*3}))\n'
        f'result = result.cut(_cutter)\n'
    )


_CUT_OUTER_SCALLOPS = ToolSpec(
    name="cut_outer_scallops",
    description=(
        "Cut N circular scallop notches around the outer perimeter at PCD positions. "
        "Use for `N-RX` outer scallop patterns (e.g. 4-R6 outer notches)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pcd_radius": {"type": "number", "description": "Center distance from origin to scallop centers"},
            "count": {"type": "integer", "description": "Number of scallops"},
            "start_angle_deg": {"type": "number", "description": "First scallop angle (default 45)"},
            "scallop_radius": {"type": "number", "description": "R value (notch radius)"},
            "part_thickness": {"type": "number", "description": "Approximate part thickness (used to size the cutter)"},
        },
        "required": ["pcd_radius", "count", "scallop_radius", "part_thickness"],
    },
    codegen=_gen_cut_outer_scallops,
)


# ---- "remove" 系: 既存形状の修復用（add-only 設計の補完） --------------------

def _gen_fill_circular_hole(args: dict) -> str:
    """既存の円形貫通穴を埋める（同じ場所により小さい/別形状の穴を後から打ち直すため）"""
    x = args["x"]
    y = args["y"]
    d = args["diameter"]
    h = args.get("part_thickness", 100)  # 部品厚以上にすれば確実に埋まる
    return (
        f'\n_filler = (cq.Workplane("XY")'
        f'.workplane(offset={-h})'
        f'.center({x}, {y}).circle({d/2}).extrude({h*3}))\n'
        f'result = result.union(_filler)\n'
    )


_FILL_CIRCULAR_HOLE = ToolSpec(
    name="fill_circular_hole",
    description=(
        "Fill (close up) an existing circular through-hole at (x, y). "
        "Use this when the candidate has a hole that is the WRONG SIZE or shape "
        "and you need to remove it before cutting a different feature in the same place. "
        "After calling this, you can call cut_obround_slot or add_hole to recut at correct dimensions."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "x": {"type": "number"},
            "y": {"type": "number"},
            "diameter": {"type": "number", "description": "Diameter of the hole to fill (slightly larger than the existing hole is safe)"},
            "part_thickness": {"type": "number", "description": "Approximate part thickness (default 100 for safety)"},
        },
        "required": ["x", "y", "diameter"],
    },
    codegen=_gen_fill_circular_hole,
)


def _gen_replace_central_hole_with_obround(args: dict) -> str:
    """中央の既存穴を埋めて、obround スロットに置き換える複合操作"""
    existing_d = args["existing_hole_diameter"]
    L = args["slot_length"]
    w = args["slot_width"]
    h = args.get("part_thickness", 100)
    return (
        f'\n# fill existing hole + cut new obround slot\n'
        f'_filler = (cq.Workplane("XY").workplane(offset={-h})'
        f'.circle({existing_d/2 + 0.5}).extrude({h*3}))\n'
        f'result = result.union(_filler)\n'
        f'result = (result.faces(">Z")'
        f'.workplane(centerOption="CenterOfBoundBox")'
        f'.slot2D(length={L}, diameter={w}).cutThruAll())\n'
    )


_REPLACE_CENTRAL_HOLE_WITH_OBROUND = ToolSpec(
    name="replace_central_hole_with_obround_slot",
    description=(
        "Replace an existing central circular hole with an obround (stadium) slot. "
        "Use this when the candidate has a wrong-sized circular hole at center but the reference "
        "specifies an obround slot in the same position. "
        "Combines fill + slot cut in one operation."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "existing_hole_diameter": {"type": "number", "description": "Diameter of the existing central hole to replace"},
            "slot_length": {"type": "number", "description": "Total length of the new obround slot"},
            "slot_width": {"type": "number", "description": "Width of the new slot"},
            "part_thickness": {"type": "number", "description": "Approximate part thickness (default 100)"},
        },
        "required": ["existing_hole_diameter", "slot_length", "slot_width"],
    },
    codegen=_gen_replace_central_hole_with_obround,
)


def _gen_resize_central_hole(args: dict) -> str:
    """既存の中央円形穴を、別の直径に置き換える"""
    existing_d = args["existing_hole_diameter"]
    new_d = args["new_diameter"]
    h = args.get("part_thickness", 100)
    return (
        f'\n# fill old hole + cut new sized hole\n'
        f'_filler = (cq.Workplane("XY").workplane(offset={-h})'
        f'.circle({existing_d/2 + 0.5}).extrude({h*3}))\n'
        f'result = result.union(_filler)\n'
        f'result = (result.faces(">Z")'
        f'.workplane(centerOption="CenterOfBoundBox").hole({new_d}))\n'
    )


_RESIZE_CENTRAL_HOLE = ToolSpec(
    name="resize_central_hole",
    description=(
        "Replace an existing central circular hole with a hole of a different diameter. "
        "Use when the candidate has the right shape (circular) but wrong size at the center."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "existing_hole_diameter": {"type": "number"},
            "new_diameter": {"type": "number"},
            "part_thickness": {"type": "number"},
        },
        "required": ["existing_hole_diameter", "new_diameter"],
    },
    codegen=_gen_resize_central_hole,
)


# ---- 全ツール集合 -------------------------------------------------------------
ALL_TOOLS: tuple[ToolSpec, ...] = (
    _ADD_HOLE,
    _ADD_PCD_HOLES,
    _CUT_OBROUND_SLOT,
    _ADD_COUNTERBORE,
    _ADD_PCD_COUNTERBORES,
    _ADD_STEP_BOSS,
    _ADD_RECESS,
    _ADD_CHAMFER_TOP_BOTTOM,
    _ADD_FILLET_VERTICAL,
    _CUT_OUTER_SCALLOPS,
    _FILL_CIRCULAR_HOLE,
    _REPLACE_CENTRAL_HOLE_WITH_OBROUND,
    _RESIZE_CENTRAL_HOLE,
)


def get_tool_definitions() -> list[dict]:
    """Anthropic tool use API に渡す JSON 配列"""
    return [t.anthropic_definition() for t in ALL_TOOLS]


def execute_tool_call(name: str, args: dict) -> str:
    """ツール名と引数から CadQuery コード片を生成"""
    for t in ALL_TOOLS:
        if t.name == name:
            return t.codegen(args)
    raise ValueError(f"Unknown tool: {name}")


def signature_for_call(name: str, args: dict) -> str | None:
    """§10.6 改善 b: ツール呼び出しの「特徴シグネチャ」を返す。

    既存特徴抽出（feature_extractor）と同じフォーマットで返すことで、
    重複検出（既存特徴に同等のエントリが既にあれば skip）が可能になる。
    None を返したツールは dedup 対象外。
    """
    if name == "add_pcd_holes":
        r = args.get("pcd_radius")
        n = args.get("count")
        d = args.get("diameter")
        if r is None or n is None or d is None:
            return None
        try:
            return f"PCD pattern: {n}× hole({d}) on PCD φ{2*float(r):.2f}"
        except (TypeError, ValueError):
            return None
    if name == "add_pcd_counterbores":
        r = args.get("pcd_radius")
        n = args.get("count")
        hd = args.get("hole_diameter")
        cd = args.get("counterbore_diameter")
        depth = args.get("counterbore_depth")
        if any(v is None for v in (r, n, hd, cd, depth)):
            return None
        try:
            return f"PCD pattern: {n}× cboreHole({hd}, {cd}, {depth}) on PCD φ{2*float(r):.2f}"
        except (TypeError, ValueError):
            return None
    if name == "add_chamfer_top_bottom":
        c = args.get("chamfer")
        return f"chamfer C{c}" if c is not None else None
    if name == "add_fillet_vertical_edges":
        r = args.get("radius")
        return f"fillet R{r}" if r is not None else None
    if name == "cut_obround_slot":
        L = args.get("length")
        w = args.get("width")
        if L is None or w is None:
            return None
        return f"obround slot: length {L} × width {w}"
    if name == "add_step_boss":
        d = args.get("diameter")
        h = args.get("height")
        if d is None or h is None:
            return None
        try:
            return f"circular boss/step φ{float(d):.2f} height {h}"
        except (TypeError, ValueError):
            return None
    return None
