"""CadQuery 公式ドキュメントの抜粋を返す検索エンジンのインターフェース。"""
from abc import ABC, abstractmethod


class ICadQueryDocsRetriever(ABC):
    """公式 docs を chunk + embedding して検索するインターフェース。

    設計手順テキストをクエリにして関連 API の抜粋を取り出し、
    生成プロンプトに注入することで「API 名の幻覚」を抑制する。
    """

    @abstractmethod
    def retrieve_text(self, query: str, top_k: int = 5, max_chars: int = 2500) -> str:
        """クエリに類似する上位ドキュメント抜粋を markdown 形式で返す。"""
        ...
