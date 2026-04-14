from dataclasses import dataclass, field
from .model_parameter import ModelParameter


@dataclass(frozen=True)
class ExecutionResult:
    """
    CadQueryスクリプト実行の結果。
    STLファイル名と、Shape から抽出した寸法パラメータを保持する。

    Attributes:
        stl_filename: 生成された STL ファイル名
        parameters: 抽出された寸法パラメータのリスト
    """
    stl_filename: str
    parameters: list[ModelParameter] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stl_filename:
            raise ValueError("stl_filename は空にできません")
