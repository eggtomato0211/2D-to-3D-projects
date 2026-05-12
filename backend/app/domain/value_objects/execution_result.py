from dataclasses import dataclass, field
from .model_parameter import ModelParameter


@dataclass(frozen=True)
class ExecutionResult:
    """
    CadQueryスクリプト実行の結果。
    STL/STEPファイル名と、Shape から抽出した寸法パラメータを保持する。

    Attributes:
        stl_filename: 生成された STL ファイル名
        parameters: 抽出された寸法パラメータのリスト
        step_filename: 生成された STEP ファイル名（線画レンダリング用、無くても可）
    """
    stl_filename: str
    parameters: list[ModelParameter] = field(default_factory=list)
    step_filename: str | None = None

    def __post_init__(self) -> None:
        if not self.stl_filename:
            raise ValueError("stl_filename は空にできません")
