from dataclasses import dataclass, field


@dataclass(frozen=True)
class YesAnswer:
    """Yes（是）の回答"""


@dataclass(frozen=True)
class NoAnswer:
    """No（否）の回答"""


@dataclass(frozen=True)
class CustomAnswer:
    """ユーザーが自由文で入力した回答"""

    text: str


ClarificationAnswer = YesAnswer | NoAnswer | CustomAnswer


@dataclass(frozen=True)
class Clarification:
    """ユーザーへの確認事項（イミュータブル）"""

    id: str  # "clarification_1", "clarification_2", ...
    question: str  # 「歯形の詳細プロファイル...標準インボリュート...仮定してよいですか？」
    candidates: tuple[ClarificationAnswer, ...] = field(default_factory=tuple)  # VLM が提案する回答候補
    user_response: ClarificationAnswer | None = None  # ユーザが入力した回答
