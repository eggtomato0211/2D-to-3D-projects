"""§10.6 Tool Use 化のツール定義 + コード生成のユニットテスト。"""
from app.infrastructure.correction_tools.tools import (
    ALL_TOOLS,
    execute_tool_call,
    get_tool_definitions,
)


def test_tool_definitions_have_required_fields():
    defs = get_tool_definitions()
    assert len(defs) >= 5
    for d in defs:
        assert "name" in d
        assert "description" in d
        assert "input_schema" in d
        assert d["input_schema"]["type"] == "object"


def test_add_hole_codegen():
    code = execute_tool_call("add_hole", {"x": 10, "y": -5, "diameter": 4.5})
    assert "result =" in code
    assert "10" in code and "-5" in code
    assert "hole(4.5)" in code
    assert '">Z"' in code  # default top


def test_add_hole_on_bottom_face():
    code = execute_tool_call("add_hole", {"x": 0, "y": 0, "diameter": 3, "on_face": "bottom"})
    assert '"<Z"' in code


def test_add_pcd_holes_codegen():
    code = execute_tool_call("add_pcd_holes", {
        "pcd_radius": 21, "count": 4, "diameter": 2.5,
    })
    assert "polarArray(radius=21" in code
    assert "count=4" in code
    assert "hole(2.5)" in code


def test_add_pcd_holes_with_partial_angle():
    code = execute_tool_call("add_pcd_holes", {
        "pcd_radius": 21, "count": 2, "diameter": 4.5,
        "start_angle_deg": 90, "total_angle_deg": 180,
    })
    assert "startAngle=90" in code
    assert "angle=180" in code


def test_cut_obround_slot_codegen():
    code = execute_tool_call("cut_obround_slot", {"length": 14, "width": 5})
    assert "slot2D(length=14, diameter=5)" in code
    assert "cutThruAll" in code


def test_add_counterbore_codegen():
    code = execute_tool_call("add_counterbore", {
        "x": 0, "y": 21, "hole_diameter": 4.5,
        "counterbore_diameter": 8.8, "counterbore_depth": 2,
    })
    assert "cboreHole(4.5, 8.8, 2)" in code
    assert '"<Z"' in code  # default back


def test_add_pcd_counterbores_codegen():
    code = execute_tool_call("add_pcd_counterbores", {
        "pcd_radius": 21, "count": 2,
        "hole_diameter": 4.5, "counterbore_diameter": 8.8,
        "counterbore_depth": 2, "total_angle_deg": 180,
    })
    assert "polarArray" in code
    assert "cboreHole(4.5, 8.8, 2)" in code


def test_add_step_boss_codegen():
    code = execute_tool_call("add_step_boss", {"diameter": 30, "height": 5})
    assert "circle(15.0)" in code
    assert "extrude(5)" in code


def test_add_recess_codegen():
    code = execute_tool_call("add_recess", {"diameter": 30, "depth": 1.5})
    assert "circle(15.0)" in code
    assert "cutBlind(-1.5)" in code


def test_add_chamfer_top_bottom():
    code = execute_tool_call("add_chamfer_top_bottom", {"chamfer": 0.5})
    assert "chamfer(0.5)" in code
    assert '">Z or <Z"' in code


def test_add_fillet_vertical():
    code = execute_tool_call("add_fillet_vertical_edges", {"radius": 3})
    assert "fillet(3)" in code
    assert '"|Z"' in code


def test_cut_outer_scallops():
    code = execute_tool_call("cut_outer_scallops", {
        "pcd_radius": 27, "count": 4, "scallop_radius": 6,
        "part_thickness": 3,
    })
    assert "polarArray(radius=27" in code
    assert "count=4" in code
    assert "circle(6)" in code
    assert "result.cut(_cutter)" in code


def test_unknown_tool_raises():
    import pytest
    with pytest.raises(ValueError):
        execute_tool_call("nonexistent_tool", {})


def test_fill_circular_hole():
    code = execute_tool_call("fill_circular_hole", {"x": 0, "y": 0, "diameter": 20})
    assert "_filler" in code
    assert "result.union(_filler)" in code


def test_replace_central_hole_with_obround():
    code = execute_tool_call("replace_central_hole_with_obround_slot", {
        "existing_hole_diameter": 20,
        "slot_length": 14,
        "slot_width": 5,
    })
    # fill 部分
    assert "_filler" in code
    assert "union" in code
    # 新スロット
    assert "slot2D(length=14, diameter=5)" in code
    assert "cutThruAll" in code


def test_resize_central_hole():
    code = execute_tool_call("resize_central_hole", {
        "existing_hole_diameter": 20,
        "new_diameter": 12,
    })
    assert "_filler" in code
    assert "union" in code
    assert "hole(12)" in code


def test_signature_for_pcd_holes_matches_extractor():
    """§10.6 改善 b: signature_for_call が feature_extractor と整合する"""
    from app.infrastructure.correction_tools.tools import signature_for_call
    from app.infrastructure.correction_tools.feature_extractor import (
        extract_existing_features,
    )
    sig = signature_for_call("add_pcd_holes", {
        "pcd_radius": 21, "count": 4, "diameter": 4.5,
    })
    # 同等の CadQuery コードを抽出すると同じシグネチャになる
    sample_script = (
        'result = result.polarArray(radius=21, startAngle=0, angle=360, count=4).hole(4.5)'
    )
    features = extract_existing_features(sample_script)
    assert sig in features, f"sig={sig!r} not in features={features}"


def test_signature_for_chamfer():
    from app.infrastructure.correction_tools.tools import signature_for_call
    sig = signature_for_call("add_chamfer_top_bottom", {"chamfer": 0.5})
    assert "C0.5" in sig


def test_signature_returns_none_for_unrecognized():
    from app.infrastructure.correction_tools.tools import signature_for_call
    assert signature_for_call("fill_circular_hole", {"x": 0, "y": 0, "diameter": 20}) is None
