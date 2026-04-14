from abc import ABC, abstractmethod
from ..value_objects.cad_script import CadScript
from ..value_objects.execution_result import ExecutionResult


class ICADExecutor(ABC):
    """
    CadQuery スクリプトを実行し、3D モデルを生成するインターフェース。
    エラー時は例外を送出する。
    """

    @abstractmethod
    def execute(self, script: CadScript) -> ExecutionResult:
        """
        CadQuery スクリプトを実行し、STL ファイルと抽出した寸法パラメータを返す。

        Args:
            script: 実行対象の CadScript

        Returns:
            ExecutionResult（STL ファイル名 + 寸法パラメータ）

        Raises:
            CadExecutionError: スクリプト実行に失敗した場合
        """
        pass
