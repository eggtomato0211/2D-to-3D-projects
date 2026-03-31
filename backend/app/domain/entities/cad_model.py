from dataclasses import dataclass
from enum import Enum
from typing import Optional

class GenerationStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"      # Step 1 実行中
    GENERATING = "generating"    # Step 2 実行中
    EXECUTING = "executing"      # Step 3 実行中
    RENDERING = "rendering"      # Step 4 実行中
    VERIFYING = "verifying"      # Step 5 実行中
    SUCCESS = "success"
    FAILED = "failed"
@dataclass
class CADModel:
    """
    生成された3Dモデルの管理情報を表すエンティティ。
    ステータス遷移（PENDING→SUCCESS/FAILED）を持ち、成果物のパスやエラー情報を保持する。
    """
    id: str
    blueprint_id: str
    status: GenerationStatus
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
