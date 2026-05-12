"""§10.6 Tool Use 改善: 既存スクリプトから現在含まれる特徴を抽出。

LLM に「既に存在する特徴」を伝えて重複追加を防ぐ。
正規表現ベースの軽量パーサ — 完全な AST 解析ではないが典型 CadQuery パターンは拾える。
"""
from __future__ import annotations

import re


def extract_existing_features(script_content: str) -> list[str]:
    """script から既存特徴を人間可読な箇条書きで返す。

    対象パターン: box / cylinder / circle+extrude / hole / cboreHole /
                  polarArray / slot2D / fillet / chamfer / cut
    """
    text = script_content
    features: list[str] = []

    # プリミティブ
    for m in re.finditer(r"\.box\(([^)]+)\)", text):
        features.append(f"primitive box({m.group(1).strip()})")
    for m in re.finditer(r"\.cylinder\(([^)]+)\)", text):
        features.append(f"primitive cylinder({m.group(1).strip()})")

    # circle + extrude → ボス・段付き
    for m in re.finditer(r"\.circle\(([\d.\-]+)\)\s*\.\s*extrude\(([\d.\-]+)\)", text):
        r = float(m.group(1))
        h = m.group(2)
        features.append(f"circular boss/step φ{2*r:.2f} height {h}")

    # circle + cutBlind → 凹み
    for m in re.finditer(r"\.circle\(([\d.\-]+)\)\s*\.\s*cutBlind\(([^)]+)\)", text):
        r = float(m.group(1))
        d = m.group(2).strip()
        features.append(f"circular recess φ{2*r:.2f} depth {d}")

    # 単発 hole（polarArray の中の hole は別途扱う）
    # まず polarArray + hole / cboreHole コンテキストを抽出
    polar_blocks: list[str] = []
    for m in re.finditer(
        r"polarArray\(([^)]+)\)[^.]*\.([\w\.]*?(?:hole|cboreHole|cskHole))\(([^)]+)\)",
        text,
    ):
        params = m.group(1)
        op = m.group(2).split(".")[-1]
        op_args = m.group(3).strip()
        # PCD radius と count を抽出
        rm = re.search(r"radius\s*=\s*([\d.\-]+)", params)
        cm = re.search(r"count\s*=\s*(\d+)", params)
        radius = rm.group(1) if rm else "?"
        count = cm.group(1) if cm else "?"
        try:
            pcd = f"φ{2*float(radius):.2f}"
        except ValueError:
            pcd = f"radius {radius}"
        features.append(f"PCD pattern: {count}× {op}({op_args}) on PCD {pcd}")
        polar_blocks.append(m.group(0))

    # polarArray コンテキストに含まれない hole / cboreHole / cskHole 単発
    text_no_polar = text
    for blk in polar_blocks:
        text_no_polar = text_no_polar.replace(blk, "")

    holes = re.findall(r"\.hole\(([\d.\-]+)\)", text_no_polar)
    if holes:
        features.append(
            f"individual hole(s): {len(holes)} count, "
            f"diameters [{', '.join(f'φ{h}' for h in holes)}]"
        )
    for m in re.finditer(
        r"\.cboreHole\(([\d.\-]+)\s*,\s*([\d.\-]+)\s*,\s*([\d.\-]+)\)",
        text_no_polar,
    ):
        d, cd, depth = m.group(1), m.group(2), m.group(3)
        features.append(f"individual counterbore: hole φ{d} + cbore φ{cd} depth {depth}")
    for m in re.finditer(
        r"\.cskHole\(([\d.\-]+)\s*,\s*([\d.\-]+)\s*,\s*([\d.\-]+)\)",
        text_no_polar,
    ):
        d, cs, depth = m.group(1), m.group(2), m.group(3)
        features.append(f"individual countersink: hole φ{d} + csk φ{cs} depth {depth}")

    # スロット
    for m in re.finditer(
        r"\.slot2D\(\s*length\s*=\s*([\d.\-]+)\s*,\s*diameter\s*=\s*([\d.\-]+)\s*\)",
        text,
    ):
        features.append(f"obround slot: length {m.group(1)} × width {m.group(2)}")

    # フィレット / 面取り
    fillets = re.findall(r"\.fillet\(([\d.\-]+)\)", text)
    if fillets:
        features.append(f"fillet R{fillets[0]} (count {len(fillets)})")
    chamfers = re.findall(r"\.chamfer\(([\d.\-]+)\)", text)
    if chamfers:
        features.append(f"chamfer C{chamfers[0]} (count {len(chamfers)})")

    # 外周切欠き的な cut 操作（_cutter / .cut(_)) の存在
    if re.search(r"result\s*=\s*\w+\s*\.\s*cut\(", text):
        # 詳細不明だが「cut が走った」を伝える
        features.append("cut operation present (likely outer scallops or pocket)")

    # 重複削除しつつ順序保存
    seen = set()
    out = []
    for f in features:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def format_existing_features(script_content: str) -> str:
    """LLM プロンプトに埋め込める形に整形して返す。"""
    feats = extract_existing_features(script_content)
    if not feats:
        return ""
    lines = ["", "## 既存スクリプトに含まれる特徴（重複追加禁止）"]
    for f in feats:
        lines.append(f"- {f}")
    lines.append("**上記と同じ特徴を再追加するツール呼び出しは禁止。**")
    lines.append("既存の値が間違っている場合は、'fill' 系ツールで埋めてから再切削する形で対応する。")
    return "\n".join(lines)
