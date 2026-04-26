from dataclasses import dataclass

@dataclass(frozen=True)
class CadScript:
    """
    VLMが生成した実行可能なCadQueryスクリプトを表す値オブジェクト。
    DesignStepの手順をもとに生成されたPythonコードを保持する。
    """

    content: str
