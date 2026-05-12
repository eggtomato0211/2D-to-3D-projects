from dataclasses import dataclass, field
from typing import Optional

from .model_parameter import ModelParameter


@dataclass(frozen=True)
class ExecutionResult:
    """CadQuery スクリプト実行の結果。

    STL ファイル名、Shape から抽出した寸法パラメータ、
    Phase 2 で必要になる STEP ファイル名（線画レンダラの入力）を保持する。
    """
    stl_filename: str
    parameters: list[ModelParameter] = field(default_factory=list)
    step_filename: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.stl_filename:
            raise ValueError("stl_filename は空にできません")
