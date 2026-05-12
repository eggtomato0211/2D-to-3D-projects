from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.clarification import (
    Clarification,
    ClarificationAnswer,
    YesAnswer,
    NoAnswer,
    CustomAnswer,
)
from app.domain.value_objects.design_step import DesignStep
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.model_parameter import ModelParameter
from app.domain.interfaces.script_generator import IScriptGenerator
from abc import abstractmethod
from typing import Optional
import re


def _answer_to_text(answer: ClarificationAnswer) -> str:
    """ClarificationAnswer を LLM プロンプトに埋め込むテキストに変換する"""
    match answer:
        case YesAnswer():
            return "はい"
        case NoAnswer():
            return "いいえ"
        case CustomAnswer(text=text):
            return text


class BaseScriptGenerator(IScriptGenerator):

    def generate(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> CadScript:
        prompt = self._build_intent_prompt(steps, clarifications)
        content = self._call_api(prompt)
        return self._parse_response(content)

    def fix_script(self, script: CadScript, feedback: str) -> CadScript:
        prompt = self._build_fix_prompt(script, feedback)
        content = self._call_api(prompt)
        return self._parse_response(content)

    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        """Phase 2-δ ループ専用: 検証で見つかった形状差分を解消する。

        runtime error 修正用の fix_script とは別プロンプトを使う。
        画像引数は基底実装では無視（テキストのみで処理）。Vision 対応の VLM 実装
        （AnthropicScriptGenerator など）はこのメソッドを override して画像を活用する。
        iteration_history（§10.3 R5）はテキストとして prompt に埋め込む。
        """
        del blueprint_image_path, line_views, shaded_views  # base 版では未使用
        prompt = self._build_correct_prompt(script, discrepancies, iteration_history)
        content = self._call_api(prompt)
        return self._parse_response(content)

    def modify_parameters(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> CadScript:
        prompt = self._build_modify_parameters_prompt(script, old_parameters, new_parameters)
        content = self._call_api(prompt)
        return self._parse_response(content)

    # RAG retriever（None なら無効）。コンストラクタで注入可能。
    _docs_retriever = None
    _ref_retriever = None  # Reference Code RAG (DeepCAD train から類似 GT)

    def _build_intent_prompt(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> str:
        """設計手順と確認事項を LLM に渡すプロンプト文字列に変換する。

        analyzer が「**【参照情報・...】**」プレフィックス付きの先頭ステップを
        挿入していた場合、それを設計手順とは別の参照セクションとして扱い、
        実際のモデリング手順は番号を振り直す（step 番号を 1 から始める）。

        さらに `_docs_retriever` が注入されている場合、CadQuery 公式ドキュメントから
        関連 API 抜粋を retrieve して system context に追加する（RAG）。
        """
        REF_PREFIX = "**【参照情報"
        reference_blocks: list[str] = []
        op_steps: list[DesignStep] = []
        for step in steps:
            if step.instruction.startswith(REF_PREFIX):
                reference_blocks.append(step.instruction)
            else:
                op_steps.append(step)

        # 実モデリングステップは 1 から振り直し
        steps_text = "\n".join(
            f"{i}. {step.instruction}"
            for i, step in enumerate(op_steps, 1)
        )

        # RAG-1: CadQuery 公式 docs 検索
        docs_block = ""
        ref_block = ""
        # 設計手順テキストをクエリにして関連 docs を retrieve
        if op_steps:
            joined_query = "\n".join(step.instruction[:200] for step in op_steps[:6])
            if self._docs_retriever is not None:
                try:
                    docs_block = self._docs_retriever.retrieve_text(
                        joined_query, top_k=5, max_chars=2500
                    )
                except Exception:
                    docs_block = ""
            # RAG-2: Reference Code 検索（参照ブロックがあれば、それを優先的にクエリにする）
            ref_query = (reference_blocks[0] if reference_blocks else joined_query)
            if self._ref_retriever is not None:
                try:
                    ref_block = self._ref_retriever.retrieve_text(
                        ref_query, top_k=3, max_chars=4000
                    )
                except Exception:
                    ref_block = ""

        prompt_parts: list[str] = []
        if docs_block:
            prompt_parts.append(
                "## CadQuery 公式ドキュメント抜粋（API シグネチャ・使用例の根拠として参照）"
            )
            prompt_parts.append(docs_block)
        if ref_block:
            prompt_parts.append(
                "## 類似 GT 部品の操作列（参照のみ。同じ操作列を真似して CadQuery で書き直すこと）"
            )
            prompt_parts.append(ref_block)
        if reference_blocks:
            prompt_parts.append(
                "## 参照情報（コード化しないこと。下記の設計手順から参照される寸法・特徴の事前整理）"
            )
            prompt_parts.extend(reference_blocks)
            prompt_parts.append(
                "## 設計手順（実際の CadQuery 操作。各ステップを順に実装すること）"
            )
        else:
            prompt_parts.append("以下の設計手順に基づいて、CadQuery スクリプトを生成してください:")
        prompt_parts.append(steps_text)
        prompt = "\n\n".join(prompt_parts)

        # ユーザーが確認した設計要件を追加（厳守指示付き）
        if clarifications:
            confirmed_clarifications = [
                c for c in clarifications
                if c.user_response is not None
            ]
            if confirmed_clarifications:
                prompt += "\n\n## 【厳守】ユーザーから確認された設計要件"
                prompt += "\n以下はユーザーが明示的に確認・指定した要件です。"
                prompt += "**絶対に簡略化せず、ユーザーの回答を忠実に反映すること。**"
                prompt += "簡単に実装できないからといって、簡略化・省略・代替形状で置き換えることは許可されません。"
                prompt += "実装が複雑になっても、ユーザー要件を優先してください。\n"
                for clarification in confirmed_clarifications:
                    prompt += f"\n- Q: {clarification.question}"
                    prompt += f"\n  A(ユーザー回答): {_answer_to_text(clarification.user_response)}"

        return prompt

    def _build_fix_prompt(self, script: CadScript, feedback: str) -> str:
        """エラー修正用のプロンプトを構築する"""
        error_hints = self._get_error_hints(feedback)
        return f"""以下の CadQuery スクリプトを実行したところエラーが発生しました。
エラーを修正したスクリプトを生成してください。

## 現在のスクリプト
```python
{script.content}
```

## エラーメッセージ
{feedback}
{error_hints}
## 修正ルール
- エラーの原因を特定し、該当箇所のみ修正すること（無関係な書き換えは禁止）
- 使用しているメソッド名・セレクタ記法に確信が持てない場合は、必ず CadQuery 公式ドキュメントを参照してください:
    - 目次:      https://cadquery-ja.readthedocs.io/ja/latest/
    - Workplane: https://cadquery-ja.readthedocs.io/ja/latest/workplane.html
    - Sketch:    https://cadquery-ja.readthedocs.io/ja/latest/sketch.html
    - Selectors: https://cadquery-ja.readthedocs.io/ja/latest/selectors.html
    - API:       https://cadquery-ja.readthedocs.io/ja/latest/apireference.html
- 記憶に頼って存在しないメソッド名を作らないこと（よくある誤り: tapHole, bore, pocket, drill, pad, .filter()）
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること（result = ... の形式）
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと
- 修正後のコードが同じエラーを起こさないことを確認すること"""

    def _build_correct_prompt(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> str:
        """Phase 2-δ: 形状差分を解消する修正版スクリプトを生成するためのプロンプト。

        runtime error ではなく『構文は正しいが図面と合わない』状況なので、
        fix_script とは別の指示文を組む。
        iteration_history（§10.3 R5）が与えられた場合、過去の試行と結果を提示して
        同じ失敗の繰り返しを防ぐ。
        """
        if not discrepancies:
            raise ValueError("discrepancies が空のとき correct_script を呼ぶべきではありません")

        crit = [d for d in discrepancies if d.severity == "critical"]
        major = [d for d in discrepancies if d.severity == "major"]
        minor = [d for d in discrepancies if d.severity == "minor"]

        # §10.2 R3: single-fix モードかどうかを総数で判別
        # （UseCase 層で 1 件に絞られた場合、prompt も 1 件専用の指示にする）
        single_fix_mode = len(discrepancies) == 1
        if single_fix_mode:
            policy_text = (
                "- **この 1 件の不一致のみを修正すること**"
                "（他の問題は次のループで扱うので無視）"
            )
        else:
            policy_text = (
                "- **Critical を全て解消すること**（最優先）\n"
                "- Major は可能な範囲で対応\n"
                "- Minor は無理に直さない（過剰な書き換えは禁止）"
            )

        def _block(label: str, items: list[Discrepancy]) -> str:
            if not items:
                return ""
            lines = [f"\n### {label} ({len(items)} 件)"]
            for i, d in enumerate(items, 1):
                # §10.0 R2: location/dimension hint があれば構造化情報として表示
                loc_line = f"\n   - 位置: {d.location_hint}" if d.location_hint else ""
                dim_line = f"\n   - 寸法: {d.dimension_hint}" if d.dimension_hint else ""
                lines.append(
                    f"{i}. **{d.feature_type}**: {d.description}\n"
                    f"   - 期待: {d.expected}\n"
                    f"   - 現状: {d.actual}"
                    f"{loc_line}{dim_line}\n"
                    f"   - 確信度: {d.confidence}"
                )
            return "\n".join(lines)

        # §10.3 R5: 過去 iter 履歴をプロンプトに埋め込む（同じ失敗を繰り返させない）
        history_block = ""
        if iteration_history:
            lines = ["\n## 過去の試行履歴（同じアプローチを繰り返さないこと）"]
            for h in iteration_history:
                tried = ", ".join(
                    f"{d.feature_type}({d.severity})" for d in h.tried_discrepancies
                ) or "(なし)"
                remaining = ", ".join(
                    f"{d.feature_type}({d.severity})" for d in h.result_discrepancies
                ) or "(なし — 解消)"
                lines.append(
                    f"- iter {h.iteration}: 修正対象=[{tried}] → 修正後の残差=[{remaining}]"
                )
            lines.append(
                "上記で **解消できなかった項目** に対しては、前回と異なるアプローチを試すこと。"
            )
            history_block = "\n".join(lines)

        return f"""以下の CadQuery スクリプトは構文的には正しく実行できますが、
生成された 3D モデルが元の図面と一致していません。
**列挙された不一致を解消する修正版スクリプト**を生成してください。

## 現在のスクリプト
```python
{script.content}
```

## 検出された不一致
{_block("Critical（必ず修正）", crit)}{_block("Major（修正すべき）", major)}{_block("Minor（余裕があれば修正）", minor)}
{history_block}

## 修正の方針
{policy_text}
- **不一致に直接関係しない箇所は触らない**（既に図面と合っている特徴を壊さない）
- 寸法・位置は元図面の値を尊重する。`位置`/`寸法` ヒントが提示されている場合は **そのまま使う**
- メソッド名・セレクタに迷ったら CadQuery 公式ドキュメントを参照:
    - 目次:      https://cadquery-ja.readthedocs.io/ja/latest/
    - Workplane: https://cadquery-ja.readthedocs.io/ja/latest/workplane.html
    - Sketch:    https://cadquery-ja.readthedocs.io/ja/latest/sketch.html
    - Selectors: https://cadquery-ja.readthedocs.io/ja/latest/selectors.html

## 出力ルール（厳守）
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること（result = ... の形式）
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと
- 修正後のコードが構文エラー無く実行できることを確認すること
- 既に正しく実装されている特徴を「念のため」改変しないこと
"""

    @staticmethod
    def _get_error_hints(feedback: str) -> str:
        """エラーメッセージからカテゴリ別のヒントを生成する"""
        hints: list[str] = []
        lower = feedback.lower()

        if "StdFail_NotDone" in feedback and "BRepAlgoAPI" in feedback:
            hints.append(
                "- ブーリアン演算（cut/union/intersect）が幾何学的に不正です。"
                "形状が交差していない、または完全包含されている可能性があります。位置関係を見直してください。"
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
                "https://cadquery-ja.readthedocs.io/ja/latest/apireference.html を参照し、"
                "API リファレンスに記載のあるメソッドだけを使ってください。"
                "よくある誤り: tapHole, bore, pocket, drill, pad, additive_extrude, .filter() は存在しません。"
                "ねじ穴は hole() / cboreHole() / cskHole() で代用してください。"
            )
        if "filter" in lower:
            hints.append(
                "- CadQuery に .filter() メソッドは存在しません。"
                "セレクタ文字列を使ってください: 面 = .faces('>Z' | '<Z' | '+X' | '%PLANE'), "
                "エッジ = .edges('|Z' | '>X' | '%CIRCLE')。"
                "詳細: https://cadquery-ja.readthedocs.io/ja/latest/selectors.html"
            )
        if "selector" in lower or "invalid selector" in lower or "ParseException" in feedback:
            hints.append(
                "- セレクタ文字列の記法が不正です（例: '>>>Z' は無効）。"
                "公式リファレンスで記法を確認してください: "
                "https://cadquery-ja.readthedocs.io/ja/latest/selectors.html"
            )
        if "no pending" in lower or "pendingWires" in feedback or "pendingEdges" in feedback:
            hints.append(
                "- pendingWires/pendingEdges が空のまま .extrude() / .loft() / .revolve() を呼んでいます。"
                "直前に .rect() / .circle() / .polygon() などで 2D 形状を作成してから 3D 生成を呼んでください。"
            )
        if "sketch" in lower and ("assemble" in lower or "face" in lower):
            hints.append(
                "- Sketch のエッジベース API（segment/arc）でワイヤーを構築した後は、"
                "face 操作の前に .assemble() を呼ぶ必要があります。"
                "詳細: https://cadquery-ja.readthedocs.io/ja/latest/sketch.html"
            )
        if "TypeError" in feedback:
            hints.append(
                "- 引数の型や数が間違っています。"
                "API リファレンスでシグネチャを確認してください: "
                "https://cadquery-ja.readthedocs.io/ja/latest/apireference.html"
            )

        if not hints:
            return ""
        return "\n## エラーのヒント\n" + "\n".join(hints) + "\n"

    def _build_system_prompt(self) -> str:
        """CadQuery コード生成用のシステムプロンプトを返す"""
        return """あなたは CadQuery の熟練エンジニアです。
与えられた設計手順に基づいて、CadQuery の Python スクリプトを生成してください。

## 公式リファレンス（メソッドの存在・シグネチャ・セレクタ記法に確信が持てない時は最優先で参照）
- 目次:      https://cadquery-ja.readthedocs.io/ja/latest/
- Workplane: https://cadquery-ja.readthedocs.io/ja/latest/workplane.html
- Sketch:    https://cadquery-ja.readthedocs.io/ja/latest/sketch.html
- Assembly:  https://cadquery-ja.readthedocs.io/ja/latest/assy.html
- Selectors: https://cadquery-ja.readthedocs.io/ja/latest/selectors.html
- API:       https://cadquery-ja.readthedocs.io/ja/latest/apireference.html
- Examples:  https://cadquery-ja.readthedocs.io/ja/latest/examples.html
記憶に頼って存在しないメソッド名を作らないこと。記憶が曖昧な場合はドキュメントに掲載されている API のみを使用してください。

## 基本ルール
- import cadquery as cq から始める
- 最終結果は result 変数に代入する（result = ... の形式）
- コードのみを出力（説明文は不要）。コードは ```python ``` で囲むこと
- 寸法の単位はすべて mm

## API レイヤの使い分け（重要）
CadQuery は 3 つの API レイヤを提供する。タスクに応じて選ぶこと。

### 1. Workplane（fluent API）— 第一選択
単一部品の段階的構築。`cq.Workplane("XY").box(...).faces(">Z").hole(...)` のようにメソッドチェーンで組む。
押し出し中心の単純なモデルはこれで完結する。

### 2. Sketch API — 複雑な 2D 輪郭が必要な場合
複数輪郭の組合せ、極座標配列、convex hull、円弧と直線の混在など Workplane の 2D 機能では辛いとき。
使用パターン:
  cq.Workplane("XY").sketch().rect(...).circle(..., mode="s").finalize().extrude(...)
ルール:
  - エッジベース API（segment/arc）でワイヤーを構築した後は **必ず .assemble() を呼ぶ**（face 化が必要）
  - 選択は自動 reset されない。次の操作前に .reset() を明示する
  - スケッチ完了後は .finalize() で Workplane に戻る

### 3. Assembly API — 複数部品の組立
`cq.Assembly()` に各部品（Workplane で作ったもの）を `.add(part, name=, loc=, color=)` し、
`.constrain(...)` で関係を定義 → `.solve()` で位置決め。単一部品なら使わない。

## Workplane の Stack 概念（誤解しやすい・最重要）
- 各 Workplane は「選択結果リスト + parent への参照」を持つ。メソッドはスタック内の各要素に自動適用される
  例: `.vertices().cboreHole(...)` はスタック上の全頂点に穴あけする
- `pendingWires` / `pendingEdges` はモデリングコンテキストで共有される
  → `.extrude()` / `.loft()` / `.revolve()` 等が呼ばれた時にこれらが消費される
  → 直前に `.rect()` / `.circle()` などで pending を作っておくこと
- 中間変数を使う時は Workplane オブジェクトを保持する（`.val()` で Solid を取り出すとチェーンが切れる）
- 過去の状態に戻るには `.end()` または `.tag("name")` + `.workplaneFromTagged("name")`
- 各点に異なる処理を適用するときは `.each(callable)` / `.eachpoint(callable, useLocalCoordinates=True)`

## セレクタ記法（faces / edges / vertices / wires に文字列で渡す）

### 方向
| 記法 | 意味 |
|---|---|
| `>X` `>Y` `>Z` | 指定軸の正方向で最も遠い要素 |
| `<X` `<Y` `<Z` | 指定軸の負方向で最も遠い要素 |
| `>>X` `<<X` | バウンディングボックス中心基準で最遠/最近 |
| `+X` `+Y` `+Z` | 法線/接線が指定軸と同方向 |
| `-X` `-Y` `-Z` | 法線/接線が指定軸と逆方向 |
| `|X` `|Y` `|Z` | 指定軸に平行 |
| `#X` `#Y` `#Z` | 指定軸に垂直 |

### 型フィルタ
`%PLANE` / `%CIRCLE` / `%LINE` / `%CYLINDER` / `%SPHERE` 等で形状型を絞り込む。

### インデックス・論理演算
- `>Z[0]` 最遠の 0 番目、`>Z[-1]` 最遠の最後
- `and` / `or` / `not` / `exc` で複合: `"|Z and >Y"`, `"not(<X or >X)"`
- 任意ベクトル: `">(1, 0, 1)"`

### 典型例
- 上面: `.faces(">Z")`
- 上面の外周エッジ: `.faces(">Z").edges()`
- Z 軸に平行なエッジ全部: `.edges("|Z")`
- 円形エッジのみ: `.edges("%CIRCLE")`
- 上面以外の全面: `.faces("not >Z")`

## ベストプラクティス
- ベース形状 → 穴・スロット → 面取り → フィレット の順に段階的に構築する
- フィレット/面取りは最後にかける（先にかけるとセレクタが崩れる）
- 複数行に分けてメソッドチェーンを書く（デバッグしやすい）
- 構築線（位置決め用）は `forConstruction=True` を付けて、その頂点に穴あけする
- `.extrude()` の引数は正の値（負が必要なら Workplane の向きを変える）
- 同じ操作を複数点に適用するときは `.pushPoints()` / `.rarray()` / `.polarArray()` / `.vertices()` を使う

## ロバストな Workplane 参照（**多段加工で頻発する `BRep_API: command not done` を防ぐ**）

材料を削った直後（cut/hole/cutBlind/cutThruAll の後）は `>Z` / `<Z` セレクタが
**直近に出現した上面/底面**を返すとは限らない（凹みの底や段差面を返すことがある）。
2 段以上のフィーチャを上面/底面に重ねる場合は **タグ + `workplaneFromTagged` で参照を固定**すること:

```python
# ❌ 危険: 凹みを切ったあとの ">Z" は凹みの底面を返す可能性がある
result = base.faces(">Z").workplane().circle(R).cutBlind(-d1)
result = result.faces(">Z").workplane().polarArray(...).hole(D)  # 凹み底面に穴を開けてしまう

# ✅ 安全: 元の上面をタグ付けしてから参照
result = base.faces(">Z").tag("top").workplaneFromTagged("top").circle(R).cutBlind(-d1)
result = result.workplaneFromTagged("top").polarArray(...).hole(D)
```

**ガイドライン**:
- ベース形状を作った直後に `result.faces(">Z").tag("top")` `result.faces("<Z").tag("bottom")` で代表面をタグ付けする
- 以降の上面操作は `.workplaneFromTagged("top")` を起点にする（`.faces(">Z").workplane()` は 1 段目のみ安全）
- `.faces(">Z[-1]")` や `.faces(">Z[1]")` でインデックス参照する場合、その面が穴あけ後にどうなるかを必ず想像する
- 段付きボス（多段押し出し）も最初にタグ付けすれば、その後の各段で `.workplaneFromTagged(...)` できる
- **3 段以上の段付き形状や、上面/底面の両方に複数フィーチャがある図面**は、**必ず**タグを使うこと

## ステップ数とスクリプト構造
- 設計手順が 8 ステップを超える場合、各ステップを **独立した `result =` 行**として書く（巨大な単一チェーンを作らない）
- 各ステップ後に `result` に再代入して状態を確定させる（中間結果のデバッグが容易）
- ある段階の操作が壊れても、次の `result =` で再構築できるよう、**毎回 result を更新**すること

## 典型コードパターン（手順に該当する形状があれば必ず使う）

### 長穴（obround / slot）の貫通切り抜き
```python
result = (
    cq.Workplane("XY").box(80, 50, 5)
    .faces(">Z").workplane()
    .slot2D(length=20, diameter=5)   # length=長さ, diameter=幅
    .cutThruAll()
)
```
※ `slot2D` の `length` は **両端中心間+幅** ではなく **両端の最外距離** を指定すること（要 API 確認）

### PCD 上に等間隔で穴を配置
```python
result = (
    cq.Workplane("XY").cylinder(height=5, radius=30)
    .faces(">Z").workplane()
    .polarArray(radius=21, startAngle=0, angle=360, count=6)
    .hole(diameter=4.5)
)
```

### 多段ボス（段付き形状）
```python
result = (
    cq.Workplane("XY").circle(25).extrude(4)        # 第一段 φ50, 高さ 4
    .faces(">Z").workplane().circle(15.925).extrude(1.5)  # 第二段 φ31.85, 高さ 1.5
    .faces(">Z").workplane().circle(15).cutBlind(-1.5)    # 中央φ30 凹み
)
```

### 表裏で異なる加工（裏よりザグリ）
```python
result = (
    cq.Workplane("XY").box(50, 50, 5)
    .faces(">Z").workplane().hole(4.5)               # 表から φ4.5 貫通
    .faces("<Z").workplane().cboreHole(4.5, 8.8, 2)  # 裏から φ8.8 のザグリ
)
```

### 全周面取り
```python
result = (
    cq.Workplane("XY").box(50, 30, 10)
    .edges(">Z or <Z").chamfer(0.5)   # 上下両エッジを面取り
)
```

### 外周スカラップ切り欠き（PCD 上に等間隔で円弧切り欠き）
```python
base = cq.Workplane("XY").circle(27).extrude(5)
cutter = (
    cq.Workplane("XY").workplane(offset=0)
    .polarArray(radius=27, startAngle=45, angle=360, count=4)
    .circle(6)            # R6 の切り欠き
    .extrude(5)
)
result = base.cut(cutter)
```

### ねじ穴の代用（タップ穴）
CadQuery には実物のねじ山生成 API は無いため、図面の `M<d>×P<p>` 表記には **下穴径での貫通穴** で代用する。下穴径の目安:
- M3 → φ2.5、M4 → φ3.3、M5 → φ4.2、M6 → φ5.0、M8 → φ6.8
```python
# 図面: M3×P0.5 貫通 → 下穴径 φ2.5 で穴あけ
result = (
    cq.Workplane("XY").box(20, 20, 5)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox")
    .hole(2.5)   # M3 のねじ下穴
)
```

### 図面記法 → コード変換早見表（典型例）
| 図面表記 | CadQuery コード片 |
|---|---|
| `2-φ4.5 PCD φ42 上下対称` | `.polarArray(radius=21, startAngle=90, angle=180, count=2).hole(4.5)` |
| `4-M3×P0.5 PCD φ42 等配` | `.polarArray(radius=21, startAngle=0, angle=360, count=4).hole(2.5)` |
| `2-φ4.5 裏よりφ8.8 サラ 深 2` | 表面側 `.hole(4.5)` + 裏面側 `.faces("<Z").workplane().cboreHole(4.5, 8.8, 2)` |
| `中央 5 幅 obround 貫通` | `.faces(">Z").workplane(centerOption="CenterOfBoundBox").slot2D(L, 5).cutThruAll()` |
| `4-R6 外周切欠き 90° 等配` | 別の `cutter` を `polarArray(radius, ..., count=4).circle(6).extrude(t)` で作って `.cut(cutter)` |
| `全周C0.5 反対側も含む` | `.edges(">Z or <Z").chamfer(0.5)` |
| `R3 縦エッジフィレット` | `.edges("|Z").fillet(3)` |

### タグ付き Workplane（多段ボス + 同じ参照面に戻る場合）
ボス追加後も**ベース上面に戻って**穴を開けたいときは `.tag()` で参照を保持。
```python
result = (
    cq.Workplane("XY").box(50, 50, 5)
    .faces(">Z").tag("base_top")     # ★ ベース上面に名前を付ける
    # ボス追加（上面が変わる）
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").circle(10).extrude(3)
    # ベース上面に戻って PCD 穴
    .workplaneFromTagged("base_top")
    .polarArray(radius=20, startAngle=0, angle=360, count=4).hole(3)
)
```

### 既存スクリプトに「足す」修正の作法（Phase 2-δ Corrector 用）
修正時は **既存の chain を壊さない** こと。よくあるアンチパターンと正解:

❌ アンチパターン: 既存全体を書き換える
```python
result = cq.Workplane("XY").circle(27).extrude(3)   # スカラップを再現せず壊した
```

✅ 正解: 既存変数に **追加の cut/union を継ぎ足す**
```python
# 既存 (これは壊さない):
# result = cq.Workplane("XY").circle(27).extrude(3) ... .cut(scallop_cutter)

# 追加: 既に正しい外周はそのままに、新たな穴だけを足す
result = (
    result
    .faces(">Z").workplane(centerOption="CenterOfBoundBox")
    .polarArray(radius=21, startAngle=0, angle=360, count=4).hole(2.5)
)
```

## よくあるエラーパターンと予防
- StdFail_NotDone（fillet/chamfer 系）: 半径がエッジ長や肉厚を超えている → 最小エッジ長の 1/3 以下を目安に
- StdFail_NotDone（boolean 系）: 形状が交差していない / 完全包含されている → 位置関係を再確認
- AttributeError: 存在しないメソッド名 → 下記許可リストにあるものだけ使う
- 結果が空 Workplane で `.extrude()` 失敗: `pendingWires` が空のまま呼んでいる → 直前に `.rect()` / `.circle()` 等を置く
- セレクタ TypeError: 記法 typo（例: `">>>Z"` は不正）→ 上の記法表に従う
- 単位混入: 必ず mm に統一。inch が来たら ×25.4 で変換

## 使用可能な主要メソッド（許可リスト・これ以外は禁止）

### Workplane の作成・移動
Workplane("XY"|"XZ"|"YZ"), workplane(offset=, invert=), faces(...).workplane(),
transformed(rotate=, offset=), center, translate, rotateAboutCenter, mirror

### プリミティブ
box, sphere, cylinder, wedge

### 2D スケッチ（Workplane 上）
rect, circle, ellipse, polygon, slot2D, text

### 2D 描画（wire 構築）
lineTo, line, vLine, hLine,
threePointArc, sagittaArc, radiusArc, tangentArcPoint, spline,
close, moveTo, move

### 3D 生成
extrude, revolve, loft, sweep, twistExtrude

### 穴・切削
hole, cboreHole, cskHole, cutBlind, cutThruAll

### 加工
fillet, chamfer, shell

### ブーリアン
cut, union, intersect, combine

### 選択
faces, edges, vertices, wires, solids, shells

### 配列
rarray, polarArray, pushPoints

### スタック制御
end, tag, workplaneFromTagged, val, vals, first, last, item, each, eachpoint, newObject, add, section

### Sketch API（cq.Sketch / Workplane.sketch())
rect, circle, polygon, regularPolygon, trapezoid, slot, ellipse, arc, segment, close, spline,
fillet, chamfer, hull,
push, distribute, rarray, parray,
faces, edges, vertices,
reset, clean, finalize, assemble, placeSketch

### Assembly API（cq.Assembly）
add, constrain, solve, save, export
制約タイプ: Point / Axis / Plane / PointInPlane / PointOnLine / Fixed / FixedPoint / FixedRotation / FixedAxis
補助: cq.Color(...), cq.Location(...)

⚠️ 以下の名前は CadQuery に存在しません（生成禁止）:
   tapHole, bore, pocket, drill, pad, additive_extrude, .filter()
⚠️ ねじ穴が必要な場合は hole() / cboreHole() / cskHole() で代用してください。"""

    def _build_modify_parameters_prompt(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> str:
        """パラメータ変更用のプロンプトを構築する"""
        changes: list[str] = []
        old_map = {p.name: p for p in old_parameters}
        for new_p in new_parameters:
            old_p = old_map.get(new_p.name)
            if old_p and old_p.value != new_p.value:
                changes.append(
                    f"- {new_p.name} ({new_p.parameter_type.value}): {old_p.value} mm → {new_p.value} mm"
                )

        changes_text = "\n".join(changes)
        return f"""以下の CadQuery スクリプトのパラメータ（寸法）を変更してください。

## 現在のスクリプト
```python
{script.content}
```

## 変更するパラメータ
{changes_text}

## ルール
- 指定されたパラメータに対応するスクリプト内の数値を変更すること
- Length はエッジの長さ、Radius は円弧・穴の半径、BoundingBox_X/Y/Z は全体の X/Y/Z 方向の寸法に対応する
- パラメータ変更に伴い、他の寸法も整合性を保つよう調整すること（例: 全体寸法を変更した場合、穴の位置なども比例的に調整）
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと"""

    def _parse_response(self, content: str) -> CadScript:
        """LLM の応答から Python コードブロックを抽出して CadScript に変換する"""
        match = re.search(r"```python\s*\n(.*?)```", content, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            code = content.strip()
        return CadScript(content=code)

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """LLM API を呼び出し、レスポンス文字列を返す"""
        pass
    


