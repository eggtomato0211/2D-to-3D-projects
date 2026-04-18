from dataclasses import dataclass


@dataclass(frozen=True)
class Clarification:
    """ユーザーへの確認事項（イミュータブル）"""

    id: str  # "clarification_1", "clarification_2", ...
    question: str  # 「歯形の詳細プロファイル...標準インボリュート...仮定してよいですか？」
    suggested_answer: str | None = None  # 推奨値（VLMから提示されることはあまりない）
    user_response: str | None = None  # ユーザが入力した回答
