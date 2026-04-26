from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.clarification import (
    Clarification,
    ClarificationAnswer,
    YesAnswer,
    NoAnswer,
    CustomAnswer,
)
from app.domain.value_objects.design_step import DesignStep
from app.domain.value_objects.model_parameter import ModelParameter
from app.domain.interfaces.script_generator import IScriptGenerator
from abc import abstractmethod
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

    def modify_parameters(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> CadScript:
        prompt = self._build_modify_parameters_prompt(script, old_parameters, new_parameters)
        content = self._call_api(prompt)
        return self._parse_response(content)

    def _build_intent_prompt(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> str:
        """設計手順と確認事項を LLM に渡すプロンプト文字列に変換する"""
        steps_text = "\n".join(
            f"{step.step_number}. {step.instruction}"
            for step in steps
        )

        prompt = f"以下の設計手順に基づいて、CadQuery スクリプトを生成してください:\n\n{steps_text}"

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
- エラーの原因を特定し、該当箇所のみ修正すること
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること（result = ... の形式）
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと
- 修正後のコードが同じエラーを起こさないことを確認すること"""

    @staticmethod
    def _get_error_hints(feedback: str) -> str:
        """エラーメッセージからカテゴリ別のヒントを生成する"""
        hints: list[str] = []

        if "StdFail_NotDone" in feedback:
            hints.append(
                "- StdFail_NotDone: fillet/chamfer の半径がエッジ長を超えている可能性があります。半径を小さくしてください。"
            )
        if "StdFail_NotDone" in feedback and "BRepAlgoAPI" in feedback:
            hints.append(
                "- ブーリアン演算が幾何学的に不正です。形状の交差・位置関係を見直してください。"
            )
        if "result" in feedback.lower() and "not found" in feedback.lower():
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
                "- 存在しないメソッド/属性を呼んでいます。CadQuery Workplane の主なメソッド: "
                "rect, circle, polygon, lineTo, line, vLine, hLine, close, moveTo, "
                "extrude, revolve, loft, sweep, hole, cboreHole, cskHole, cutBlind, cutThruAll, "
                "fillet, chamfer, shell, cut, union, intersect, faces, edges, vertices, "
                "workplane, center, translate, rarray, polarArray, pushPoints。"
                "tapHole, bore, pocket, drill, pad, filter 等は存在しません。"
            )
        if "filter" in feedback.lower():
            hints.append(
                "- CadQuery に .filter() メソッドは存在しません。"
                "面の選択には .faces('>Z'), .faces('<Z'), .faces('+X') 等のセレクタ文字列を使ってください。"
                "エッジの選択には .edges('|Z'), .edges('>X') 等を使ってください。"
            )
        if "TypeError" in feedback:
            hints.append(
                "- 引数の型や数が間違っています。メソッドのシグネチャを確認してください。"
            )

        if not hints:
            return ""
        return "\n## エラーのヒント\n" + "\n".join(hints) + "\n"

    def _build_system_prompt(self) -> str:
        """CadQuery コード生成用のシステムプロンプトを返す"""
        return """あなたは CadQuery の熟練エンジニアです。
与えられた設計手順に基づいて、CadQuery の Python スクリプトを生成してください。

## 基本ルール
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること（result = ... の形式）
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと
- 寸法の単位はすべて mm とする

## CadQuery ベストプラクティス
- Workplane のメソッドチェーンを途切れさせないこと（中間変数を使う場合は Workplane オブジェクトを保持）
- fillet / chamfer はエッジ長より小さい半径を指定すること（大きすぎると StdFail_NotDone エラーになる）
- 穴あけには .hole() または .cutThruAll() を使い、貫通方向を意識すること
- .faces(">Z"), .edges("|X") などのセレクタ文字列は CadQuery の仕様に厳密に従うこと
- ブーリアン演算（cut, union, intersect）の対象は同じ型の Workplane / Solid であること
- 複雑な形状は一度に作らず、ベース形状 → 加工（穴・面取り等）の順で段階的に構築すること
- .extrude() の引数は正の値を使うこと（負の値が必要な場合は Workplane の向きを変える）
- .rect(), .circle() 等の 2D スケッチは .extrude() や .cutBlind() の前に配置すること

## 使用可能な Workplane メソッド一覧（これ以外のメソッドは存在しないため使用禁止）

### 2D スケッチ
rect, circle, ellipse, polygon, slot2D, text

### 2D 描画（wire）
lineTo, line, vLine, hLine, threePointArc, sagittaArc, radiusArc, tangentArcPoint, spline, close, moveTo, move

### 3D 生成
extrude, revolve, loft, sweep, twistExtrude

### 穴・切削
hole, cboreHole, cskHole, cutBlind, cutThruAll

### 加工
fillet, chamfer, shell

### ブーリアン演算
cut, union, intersect

### 面・エッジ選択
faces, edges, vertices, wires, solids, shells

### 座標・Workplane 操作
workplane, transformed, center, translate, rotateAboutCenter, mirror

### 配列
rarray, polarArray, pushPoints

### その他
val, vals, first, last, item, tag, end, each, eachpoint, newObject, add, combine, section

⚠️ tapHole, bore, pocket, drill, pad, additive_extrude 等の名前は CadQuery に存在しません。
⚠️ ねじ穴が必要な場合は hole() または cboreHole() / cskHole() で代用してください。"""

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
    


