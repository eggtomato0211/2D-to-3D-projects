"""類似 GT 部品の操作列を返す検索エンジンのインターフェース。"""
from abc import ABC, abstractmethod


class IReferenceCodeRetriever(ABC):
    """DeepCAD 等から構築された参照コーパスを検索するインターフェース。

    生成プロンプトの文脈として「似た部品はこういう操作列だった」を注入することで
    モデルが書く CadQuery のパターン精度を上げる。
    具体実装は infrastructure/rag/ に置く。
    """

    @abstractmethod
    def retrieve_text(self, query: str, top_k: int = 3, max_chars: int = 4000) -> str:
        """クエリに類似する上位エントリを markdown 抜粋として返す。"""
        ...

    @abstractmethod
    def set_exclude_ids(self, ids: set[str]) -> None:
        """評価時にリーク防止用、retrieve から除外する ID 集合を設定する。"""
        ...
