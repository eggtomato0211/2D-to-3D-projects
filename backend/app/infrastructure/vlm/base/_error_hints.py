"""ランタイムエラー文字列 → 修正ヒントの組み立て。

fix_script 用のプロンプトに具体的な対処法を埋め込んで、
同じエラーを繰り返し起こさないようにする。
"""
from __future__ import annotations


def error_hints_for(feedback: str) -> str:
    """エラーメッセージから該当する修正ヒントを連結して返す。

    返り値は markdown 形式の "## エラーのヒント" セクション、ヒントが
    無ければ空文字列。
    """
    hints: list[str] = []
    lower = feedback.lower()

    if "StdFail_NotDone" in feedback and "BRepAlgoAPI" in feedback:
        hints.append(
            "- ブーリアン演算（cut/union/intersect）が幾何学的に不正です。"
            "形状が交差していない、または完全包含されている可能性があります。"
            "位置関係を見直してください。"
        )
    elif "StdFail_NotDone" in feedback:
        hints.append(
            "- StdFail_NotDone: fillet/chamfer の半径がエッジ長や肉厚を超えている可能性があります。"
            "対象エッジの最小長の 1/3 以下を目安に半径を小さくしてください。"
        )
    if "result" in lower and "not found" in lower:
        hints.append(
            "- result 変数が定義されていません。最終形状を result = ... で代入してください。"
        )
    if "SyntaxError" in feedback:
        hints.append(
            "- Python の構文エラーです。括弧の対応、インデント、コロンの有無を確認してください。"
        )
    if "NameError" in feedback:
        hints.append(
            "- 未定義の変数・関数を参照しています。変数名のタイポや定義順を確認してください。"
        )
    if "AttributeError" in feedback:
        hints.append(
            "- 存在しないメソッド/属性を呼んでいます。"
            "API リファレンス (https://cadquery-ja.readthedocs.io/ja/latest/apireference.html) "
            "に記載のあるメソッドだけを使ってください。"
            "よくある誤り: tapHole, bore, pocket, drill, pad, .filter() は存在しません。"
            "ねじ穴は hole() / cboreHole() / cskHole() で代用してください。"
        )
    if "filter" in lower:
        hints.append(
            "- CadQuery に .filter() メソッドは存在しません。セレクタ文字列を使用すること: "
            "面 = .faces('>Z' | '<Z' | '+X' | '%PLANE'), "
            "エッジ = .edges('|Z' | '>X' | '%CIRCLE')。"
        )
    if "ParseException" in feedback or "invalid selector" in lower:
        hints.append(
            "- セレクタ文字列の記法が不正です（例: '>>>Z' は無効）。"
            "公式リファレンスで記法を確認してください: "
            "https://cadquery-ja.readthedocs.io/ja/latest/selectors.html"
        )
    if "no pending" in lower or "pendingWires" in feedback or "pendingEdges" in feedback:
        hints.append(
            "- pendingWires/pendingEdges が空のまま .extrude() / .loft() / .revolve() を呼んでいます。"
            "直前に .rect() / .circle() / .polygon() などで 2D 形状を作成してください。"
        )
    if "sketch" in lower and ("assemble" in lower or "face" in lower):
        hints.append(
            "- Sketch のエッジベース API（segment/arc）でワイヤーを構築した後は、"
            "face 操作の前に .assemble() を呼ぶ必要があります。"
        )
    if "TypeError" in feedback:
        hints.append(
            "- 引数の型や数が間違っています。"
            "API リファレンスでシグネチャを確認してください。"
        )

    if not hints:
        return ""
    return "\n## エラーのヒント\n" + "\n".join(hints) + "\n"
