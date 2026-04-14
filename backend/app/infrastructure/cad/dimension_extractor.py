"""
CadQuery の Workplane / Shape オブジェクトから寸法パラメータを抽出する。

OCCT の B-Rep 情報を利用して、エッジの長さ・円弧半径・バウンディングボックスを取得する。
STL（メッシュ）ではなく B-Rep を解析するため、正確な寸法が得られる。

エッジの位置・方向・隣接面から意味のある日本語名を自動生成する。
"""

import math
import cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.GCPnts import GCPnts_AbscissaPoint, GCPnts_UniformAbscissa
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.GeomAbs import (
    GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse,
    GeomAbs_Cylinder, GeomAbs_Plane,
)
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape

from app.domain.value_objects.model_parameter import ModelParameter, ParameterType


# --- 座標抽出ユーティリティ ---

def _edge_sample_points(adaptor: BRepAdaptor_Curve, n: int = 16) -> list[list[float]]:
    """エッジ上の等間隔サンプル点を返す（ハイライト描画用）"""
    u_start = adaptor.FirstParameter()
    u_end = adaptor.LastParameter()

    if adaptor.GetType() == GeomAbs_Line:
        # 直線は始点・終点の2点で十分
        p0 = adaptor.Value(u_start)
        p1 = adaptor.Value(u_end)
        return [
            [round(p0.X(), 2), round(p0.Y(), 2), round(p0.Z(), 2)],
            [round(p1.X(), 2), round(p1.Y(), 2), round(p1.Z(), 2)],
        ]

    # 曲線はn点でサンプリング
    points: list[list[float]] = []
    for i in range(n + 1):
        u = u_start + (u_end - u_start) * i / n
        p = adaptor.Value(u)
        points.append([round(p.X(), 2), round(p.Y(), 2), round(p.Z(), 2)])
    return points


def _edge_midpoint(adaptor: BRepAdaptor_Curve) -> tuple[float, float, float]:
    """エッジの中点座標を返す"""
    u_mid = (adaptor.FirstParameter() + adaptor.LastParameter()) / 2.0
    p = adaptor.Value(u_mid)
    return (round(p.X(), 2), round(p.Y(), 2), round(p.Z(), 2))


# --- 面の法線方向ラベル ---

_FACE_LABELS = {
    (0, 0, 1): "上面",
    (0, 0, -1): "底面",
    (1, 0, 0): "右側面",
    (-1, 0, 0): "左側面",
    (0, 1, 0): "前面",
    (0, -1, 0): "背面",
}


def _quantize_direction(x: float, y: float, z: float) -> tuple[int, int, int]:
    """方向ベクトルを最も近い軸方向に丸める"""
    ax, ay, az = abs(x), abs(y), abs(z)
    if ax >= ay and ax >= az:
        return (1 if x > 0 else -1, 0, 0)
    elif ay >= ax and ay >= az:
        return (0, 1 if y > 0 else -1, 0)
    else:
        return (0, 0, 1 if z > 0 else -1)


def _face_label_from_normal(nx: float, ny: float, nz: float) -> str | None:
    """面の法線から位置ラベルを取得"""
    q = _quantize_direction(nx, ny, nz)
    return _FACE_LABELS.get(q)


def _build_ancestor_map(shape) -> TopTools_IndexedDataMapOfShapeListOfShape:
    """Shape 全体のエッジ→隣接面マップを一度だけ構築する"""
    m = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape, TopAbs_EDGE, TopAbs_FACE, m)
    return m


def _get_adjacent_face_labels(edge, ancestor_map: TopTools_IndexedDataMapOfShapeListOfShape) -> list[str]:
    """エッジに隣接する面の位置ラベルを取得する"""
    labels: list[str] = []

    edge_map_index = None
    for i in range(1, ancestor_map.Extent() + 1):
        if ancestor_map.FindKey(i).IsSame(edge.wrapped):
            edge_map_index = i
            break

    if edge_map_index is None:
        return labels

    faces = ancestor_map.FindFromIndex(edge_map_index)
    for shape_item in faces:
        face = TopoDS.Face_s(shape_item)
        surf = BRepAdaptor_Surface(face)
        if surf.GetType() == GeomAbs_Plane:
            plane = surf.Plane()
            d = plane.Axis().Direction()
            label = _face_label_from_normal(d.X(), d.Y(), d.Z())
            if label:
                labels.append(label)
        elif surf.GetType() == GeomAbs_Cylinder:
            labels.append("円筒面")

    return labels


def _edge_direction_label(adaptor: BRepAdaptor_Curve) -> str:
    """直線エッジの方向ラベルを返す"""
    p0 = adaptor.Value(adaptor.FirstParameter())
    p1 = adaptor.Value(adaptor.LastParameter())
    dx, dy, dz = p1.X() - p0.X(), p1.Y() - p0.Y(), p1.Z() - p0.Z()
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-9:
        return ""
    dx, dy, dz = dx / length, dy / length, dz / length
    q = _quantize_direction(dx, dy, dz)
    direction_map = {
        (1, 0, 0): "X方向",
        (-1, 0, 0): "X方向",
        (0, 1, 0): "Y方向",
        (0, -1, 0): "Y方向",
        (0, 0, 1): "Z方向",
        (0, 0, -1): "Z方向",
    }
    return direction_map.get(q, "")


def _build_line_name(
    adaptor: BRepAdaptor_Curve,
    edge,
    ancestor_map: TopTools_IndexedDataMapOfShapeListOfShape,
    seen_names: dict[str, int],
) -> str:
    """直線エッジの意味のある名前を生成する"""
    face_labels = _get_adjacent_face_labels(edge, ancestor_map)
    direction = _edge_direction_label(adaptor)

    if face_labels:
        location = face_labels[0]
    else:
        # 面ラベルが取れない場合はバウンディングボックス内の位置で判断
        mid = _edge_midpoint(adaptor)
        location = f"({mid[0]:.0f},{mid[1]:.0f},{mid[2]:.0f})"

    base_name = f"{location} {direction}エッジ" if direction else f"{location} エッジ"

    # 同名の重複回避
    if base_name in seen_names:
        seen_names[base_name] += 1
        return f"{base_name} #{seen_names[base_name]}"
    else:
        seen_names[base_name] = 1
        return base_name


def _build_circle_name(
    adaptor: BRepAdaptor_Curve,
    edge,
    ancestor_map: TopTools_IndexedDataMapOfShapeListOfShape,
    seen_names: dict[str, int],
) -> str:
    """円弧/円エッジの意味のある名前を生成する"""
    face_labels = _get_adjacent_face_labels(edge, ancestor_map)

    # 円筒面に隣接していたら「穴」系
    is_hole = "円筒面" in face_labels
    plane_labels = [l for l in face_labels if l != "円筒面"]

    if is_hole:
        location = plane_labels[0] if plane_labels else ""
        base_name = f"{location}の穴".lstrip("の") if location else "穴"
    else:
        location = plane_labels[0] if plane_labels else ""
        base_name = f"{location}の円弧".lstrip("の") if location else "円弧"

    if base_name in seen_names:
        seen_names[base_name] += 1
        return f"{base_name} #{seen_names[base_name]}"
    else:
        seen_names[base_name] = 1
        return base_name


# --- メインの抽出関数 ---

def extract_parameters(result: cq.Workplane) -> list[ModelParameter]:
    """
    CadQuery Workplane から寸法パラメータを抽出する。

    抽出対象:
    - バウンディングボックス（X, Y, Z 寸法）
    - 直線エッジの長さ（重複排除済み、幾何学的コンテキスト命名）
    - 円弧・円エッジの半径（重複排除済み、穴/円弧の自動判別）

    各パラメータにエッジの3D座標を付与し、フロントエンドでのハイライト表示に利用する。
    """
    parameters: list[ModelParameter] = []
    solid = result.val()
    shape = solid.wrapped
    bb = solid.BoundingBox()

    # --- バウンディングボックス ---
    # エッジポイント: バウンディングボックスの各辺をハイライト用に生成
    cx, cy, cz = bb.center.x, bb.center.y, bb.center.z
    parameters.append(ModelParameter(
        name="全幅 (X)",
        value=round(bb.xlen, 3),
        parameter_type=ParameterType.BOUNDING_X,
        edge_points=[
            [round(bb.xmin, 2), round(cy, 2), round(bb.zmin, 2)],
            [round(bb.xmax, 2), round(cy, 2), round(bb.zmin, 2)],
        ],
    ))
    parameters.append(ModelParameter(
        name="奥行 (Y)",
        value=round(bb.ylen, 3),
        parameter_type=ParameterType.BOUNDING_Y,
        edge_points=[
            [round(bb.xmin, 2), round(bb.ymin, 2), round(bb.zmin, 2)],
            [round(bb.xmin, 2), round(bb.ymax, 2), round(bb.zmin, 2)],
        ],
    ))
    parameters.append(ModelParameter(
        name="高さ (Z)",
        value=round(bb.zlen, 3),
        parameter_type=ParameterType.BOUNDING_Z,
        edge_points=[
            [round(bb.xmin, 2), round(bb.ymin, 2), round(bb.zmin, 2)],
            [round(bb.xmin, 2), round(bb.ymin, 2), round(bb.zmax, 2)],
        ],
    ))

    # --- エッジ解析 ---
    ancestor_map = _build_ancestor_map(shape)
    edges = result.edges().vals()
    seen_lengths: dict[float, list[list[list[float]]]] = {}
    seen_radii: dict[float, list[list[list[float]]]] = {}
    seen_names: dict[str, int] = {}

    line_params: list[tuple[str, float, list[list[float]]]] = []
    circle_params: list[tuple[str, float, list[list[float]]]] = []

    for edge in edges:
        adaptor = BRepAdaptor_Curve(edge.wrapped)
        curve_type = adaptor.GetType()

        if curve_type == GeomAbs_Line:
            length = round(GCPnts_AbscissaPoint.Length_s(adaptor), 3)
            if length <= 0:
                continue
            points = _edge_sample_points(adaptor)
            if length not in seen_lengths:
                seen_lengths[length] = [points]
                name = _build_line_name(adaptor, edge, ancestor_map, seen_names)
                line_params.append((name, length, points))
            else:
                seen_lengths[length].append(points)

        elif curve_type == GeomAbs_Circle:
            circle = adaptor.Circle()
            radius = round(circle.Radius(), 3)
            if radius <= 0:
                continue
            points = _edge_sample_points(adaptor)
            if radius not in seen_radii:
                seen_radii[radius] = [points]
                name = _build_circle_name(adaptor, edge, ancestor_map, seen_names)
                circle_params.append((name, radius, points))
            else:
                seen_radii[radius].append(points)

    # パラメータ生成（代表エッジの座標を使用）
    for name, length, points in line_params:
        parameters.append(ModelParameter(
            name=name,
            value=length,
            parameter_type=ParameterType.LENGTH,
            edge_points=points,
        ))

    for name, radius, points in circle_params:
        parameters.append(ModelParameter(
            name=name,
            value=radius,
            parameter_type=ParameterType.RADIUS,
            edge_points=points,
        ))

    return parameters
