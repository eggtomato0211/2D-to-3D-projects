"""§10.6: 既存特徴抽出のユニットテスト。"""
from app.infrastructure.correction_tools.feature_extractor import (
    extract_existing_features,
    format_existing_features,
)


def test_extract_box_only():
    feats = extract_existing_features('result = cq.Workplane("XY").box(80, 50, 20)')
    assert any("box(80, 50, 20)" in f for f in feats)


def test_extract_individual_holes():
    feats = extract_existing_features("""
result = (
    cq.Workplane("XY").box(80, 50, 20)
    .faces(">Z").workplane().hole(12)
    .faces(">Z").workplane().center(25, 0).hole(6)
)
""")
    holes = [f for f in feats if "individual hole" in f]
    assert holes, f"expected individual hole entry, got {feats}"
    assert "φ12" in holes[0] and "φ6" in holes[0]


def test_extract_pcd_pattern():
    feats = extract_existing_features("""
result = result.polarArray(radius=21, startAngle=0, angle=360, count=4).hole(4.5)
""")
    pcd = [f for f in feats if "PCD pattern" in f]
    assert pcd
    assert "4×" in pcd[0]  # count
    assert "φ42" in pcd[0]  # 2 * 21


def test_extract_counterbore():
    feats = extract_existing_features("""
result = result.faces("<Z").workplane().center(0, 21).cboreHole(4.5, 8.8, 2)
""")
    cb = [f for f in feats if "counterbore" in f]
    assert cb
    assert "φ4.5" in cb[0] and "φ8.8" in cb[0]


def test_extract_slot():
    feats = extract_existing_features("""
result = result.faces(">Z").workplane().slot2D(length=14, diameter=5).cutThruAll()
""")
    slot = [f for f in feats if "obround slot" in f]
    assert slot
    assert "14" in slot[0] and "5" in slot[0]


def test_extract_fillet_chamfer():
    feats = extract_existing_features("""
result = result.edges("|Z").fillet(3).edges(">Z or <Z").chamfer(0.5)
""")
    assert any("fillet R3" in f for f in feats)
    assert any("chamfer C0.5" in f for f in feats)


def test_extract_circular_boss():
    feats = extract_existing_features("""
result = result.faces(">Z").workplane().circle(15).extrude(5)
""")
    boss = [f for f in feats if "circular boss" in f]
    assert boss
    assert "φ30" in boss[0]


def test_format_returns_empty_when_no_features():
    out = format_existing_features("import cadquery as cq")
    assert out == ""


def test_format_includes_warning_text():
    out = format_existing_features("result = cq.Workplane('XY').box(10, 10, 10)")
    assert "重複追加禁止" in out
    assert "box" in out


def test_dedup_features():
    """同じ特徴の重複は 1 件にまとめる"""
    feats = extract_existing_features("""
result = result.fillet(3).fillet(3).fillet(3)
""")
    fillet_count = sum(1 for f in feats if "fillet" in f)
    assert fillet_count == 1
