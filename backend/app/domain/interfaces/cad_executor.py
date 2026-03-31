from abc import ABC, abstractmethod
from ..value_objects.cad_script import CadScript


class ICADExecutor(ABC):
    """
    CadQuery スクリプトを実行し、3D モデルを生成するインターフェース。
    エラー時は例外を送出する。
    """

    @abstractmethod
    def execute(self, script: CadScript) -> str:
        """
        CadQuery スクリプトを実行し、生成された STL ファイルのパスを返す。
        外部サービスの実装では実ファイルシステムに保存。

        Args:
            script: 実行対象の CadScript

        Returns:
            生成された STL ファイルのパス

        Raises:
            CadExecutionError: スクリプト実行に失敗した場合
        """
        pass
