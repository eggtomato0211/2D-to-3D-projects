from dataclasses import dataclass
from typing import Optional

@dataclass
class Blueprint:
    """
    ユーザーがアップロードした2D図面を表すエンティティ。
    すべての処理の起点となり、図面ファイルのメタ情報を保持する。
    """
    id: str
    file_path: str
    file_name: str
    content_type: str = "image/png"
    
